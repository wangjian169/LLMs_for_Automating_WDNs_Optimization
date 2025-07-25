from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, register_function
from settings.llms import llm_config
from settings.functions import calibration_read_information,pump_read_information,simulation_objective_calibration,simulation_objective_pump
from settings.prompts import calibration_orchestrating,modelling_calibration,pump_orchestrating,modelling_pump

def main(modelling_prompts,orchestrating_prompts,initial_chat,task):
    modelling_agent = AssistantAgent(
        name="Modeller",
        llm_config=llm_config,
        system_message= modelling_prompts,
    )

    orchestrating_agent = AssistantAgent(
        name="Hydraulic_Expert",
        llm_config=llm_config,
        system_message= orchestrating_prompts)

    user_proxy = UserProxyAgent(
        name="Executor",
        llm_config=False,
        human_input_mode="NEVER",
        code_execution_config={"last_n_messages": 10, "work_dir": "coding", "use_docker": False},
    )
    if task =='hydraulic model calibration':
        register_function(
            simulation_objective_calibration,
            caller=modelling_agent,
            executor=user_proxy,
            name="simulation_objective",
            description="Simulate water network pressure based on new roughness values and calculate the error."
        )
    elif task =='pump operation cost optimization':
        register_function(
            simulation_objective_pump,
            caller=modelling_agent,
            executor=user_proxy,
            name="simulation_objective",
            description="Simulate water network pressure based on new pump speed values and calculate the error."
        )

    groupchat = GroupChat(agents=[orchestrating_agent, modelling_agent, user_proxy],
                          messages=[], max_round=30, speaker_selection_method='round_robin')
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    response = user_proxy.initiate_chat(
        manager,
        message=initial_chat
    )

    return response

if __name__ == "__main__":
    # hydraulic model calibration for net2
    calibration_pipe_info, correct_pressure, initial_pressure, demand, mse, mae = calibration_read_information(
        original_path='networks/net2_initial.inp', real_path='networks/net2.inp')
    calibration_initial_chat = f'''Initial data loaded:
            - Pipe information: {calibration_pipe_info}
            - Actual network pressure: {correct_pressure.to_dict()}
            - Initial simulated pressure: {initial_pressure.to_dict()}
            - Water demand for junctions: {demand.to_dict()}
            - Initial MSE: {mse}
            - Initial MAE: {mae}

        Task: Correction of pipe roughness.
        Record adjustment history: Save the current roughness state after each adjustment for easy backtracking.'''
    main(modelling_calibration, calibration_orchestrating, calibration_initial_chat,task='hydraulic model calibration')

    # hydraulic model calibration for anytown

    calibration_pipe_info, correct_pressure, initial_pressure, demand, mse, mae = calibration_read_information(
        original_path='networks/Anytown_initial.inp.inp', real_path='networks/Anytown.inp')
    calibration_initial_chat = f'''Initial data loaded:
                - Pipe information: {calibration_pipe_info}
                - Actual network pressure: {correct_pressure.to_dict()}
                - Initial simulated pressure: {initial_pressure.to_dict()}
                - Water demand for junctions: {demand.to_dict()}
                - Initial MSE: {mse}
                - Initial MAE: {mae}

            Task: Correction of pipe roughness.
            Record adjustment history: Save the current roughness state after each adjustment for easy backtracking.'''
    main(modelling_calibration, calibration_orchestrating, calibration_initial_chat,task='hydraulic model calibration')

    # pump operation cost optimization for anytown

    pump_pipe_info, energy, price = pump_read_information(file_path='networks/Anytown.inp')
    pump_initial_chat = f'''Initial data loaded:
            - Initial pump energy: {energy.to_dict()}
            - Initial pump speed for each time: 1.0
            - Water network information: {pump_pipe_info}
            - Initial operation price: {price}
            - Electricity price pattern a day: ￡/kwh：[0.1, 0.1, 0.15, 0.15, 0.2, 0.2, 0.15, 0.1, 0.1]

        Task: Optimize the pump speed to reduce pump operation price.
        Record adjustment history: Save the current speed state after each adjustment for easy backtracking'''
    main(modelling_pump, pump_orchestrating, pump_initial_chat,task='pump operation cost optimization')