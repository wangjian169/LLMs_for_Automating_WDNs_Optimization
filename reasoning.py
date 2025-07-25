from autogen import AssistantAgent
from settings.llms import llm_config
from settings.functions import calibration_read_information,pump_read_information
from settings.prompts import calibration_orchestrating,reasoning_calibration_knowledge,pump_orchestrating,reasoning_pump_knowledge


def main(knowledge_prompts,orchestrating_prompts,initial_chat):
    knowledge_agent = AssistantAgent(
        name="Calculator",
        llm_config=llm_config,
        system_message= knowledge_prompts,
    )

    orchestrating_agent = AssistantAgent(
        name="Hydraulic_Expert",
        llm_config=llm_config,
        system_message= orchestrating_prompts)

    response = knowledge_agent.initiate_chat(
        orchestrating_agent,
        message=initial_chat,
        max_turns=5)

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
    main(reasoning_calibration_knowledge,calibration_orchestrating,calibration_initial_chat)

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
    main(reasoning_calibration_knowledge, calibration_orchestrating, calibration_initial_chat)

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
    main(reasoning_pump_knowledge, pump_orchestrating, pump_initial_chat)