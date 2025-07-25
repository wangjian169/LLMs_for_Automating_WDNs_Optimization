from autogen import AssistantAgent, UserProxyAgent
from settings.llms import llm_config
from settings.prompts import calibration_coding_orchestrating,calibration_coding_executor,pump_coding_executor,pump_coding_orchestrating

def main(coding_prompts,orchestrating_prompts,initial_chat):

    coder = AssistantAgent(
        name="Coder",
        llm_config=llm_config,
        system_message=orchestrating_prompts,
    )

    user = UserProxyAgent(
        name="Exectuor",
        system_message=coding_prompts,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config={"last_n_messages": 5, "work_dir": "coding", "use_docker": False}
    )


    response = user.initiate_chat(
        coder,
        message=initial_chat,
        max_turns=5
    )

    return response

calibration_initial_chat_net2 = '''Task: Hydraulic Network Roughness Calibration

                        Input Data:
                        - **Hydraulic Network Model**: `../networks/net2_initial.inp`
                        - **Real Pressure Data**: `../networks/net2_pressure.csv`
                        - **Simulation Function**: `from functions import simulation_objective_calibration` 
                        (Simulates the hydraulic network pressure after updating pipe roughness values.
                                Parameters:
                                ----------
                                new_roughness : dict
                                    A dictionary containing the updated roughness values for specific pipes.
                                    - **Keys (str):** Pipe names (must match those defined in the network model).
                                    - **Values (float):** Assigned roughness values (typically between 50 and 150).

                                    Example:
                                    ```python
                                    {
                                        'pipe1': 100,
                                        'pipe2': 90,
                                        'pipe3': 110
                                    }
                                    ```

                                wn : wntr.network.WaterNetworkModel
                                        The EPANET water network model instance.

                                Returns:
                                -------
                                pandas.DataFrame
                                    A DataFrame containing the simulated pressure values at each node after applying
                                    the updated roughness values. The output structure is as follows:

                                    - **Index:** Node names
                                    - **Columns:** Time steps
                                    - **Values:** Pressure values at each node over time

                                    Example Output:
                                    ```
                                            0        3600     7200     10800
                                    Node1  45.3     46.1     47.0     48.2
                                    Node2  50.0     50.8     51.5     52.1
                                    Node3  39.7     40.2     40.9     41.5
                                    ```)

                        Objective:
                        - Use **`WNTR`** to read `Anytown_initial.inp` and perform a **hydraulic simulation** to obtain **simulated pressure data**.
                        - Load `pressure.csv` to get **real observed pressure values**.
                        - **Compute pressure errors**: Compare **simulated pressure** with **real pressure** using **MAE (Mean Absolute Error)**.
                        - **Roughness Adjustment**:
                          - Implement an **Optimization algorithm** to iteratively adjust pipe roughness.
                          - Ensure roughness values remain within a **valid range (60–140)**.
                          - Set `maxiter=50` in the optimizer, only when the number of iterations is reached, the optimization stops.
                          - Don't save files, just Print the result of **50 iteration step** during optimization (e.g., all 50 iterations); Example:`Iteration <n>: MAE = <value> `; and final roughness of each pipes'''
calibration_initial_chat_anytown = '''Task: Hydraulic Network Roughness Calibration

                Input Data:
                - **Hydraulic Network Model**: `../networks/Anytown_initial.inp`
                - **Real Pressure Data**: `../networks/pressure.csv`
                - **Simulation Function**: `from functions import simulation_objective_calibration` 
                (Simulates the hydraulic network pressure after updating pipe roughness values.
                        Parameters:
                        ----------
                        new_roughness : dict
                            A dictionary containing the updated roughness values for specific pipes.
                            - **Keys (str):** Pipe names (must match those defined in the network model).
                            - **Values (float):** Assigned roughness values (typically between 50 and 150).

                            Example:
                            ```python
                            {
                                'pipe1': 100,
                                'pipe2': 90,
                                'pipe3': 110
                            }
                            ```

                        wn : wntr.network.WaterNetworkModel
                                The EPANET water network model instance.

                        Returns:
                        -------
                        pandas.DataFrame
                            A DataFrame containing the simulated pressure values at each node after applying
                            the updated roughness values. The output structure is as follows:

                            - **Index:** Node names
                            - **Columns:** Time steps
                            - **Values:** Pressure values at each node over time

                            Example Output:
                            ```
                                    0        3600     7200     10800
                            Node1  45.3     46.1     47.0     48.2
                            Node2  50.0     50.8     51.5     52.1
                            Node3  39.7     40.2     40.9     41.5
                            ```)

                Objective:
                - Use **`WNTR`** to read `Anytown_initial.inp` and perform a **hydraulic simulation** to obtain **simulated pressure data**.
                - Load `pressure.csv` to get **real observed pressure values**.
                - **Compute pressure errors**: Compare **simulated pressure** with **real pressure** using **MAE (Mean Absolute Error)**.
                - **Roughness Adjustment**:
                  - Implement an **Optimization algorithm** to iteratively adjust pipe roughness.
                  - Ensure roughness values remain within a **valid range (60–140)**.
                  - Set `maxiter=50` in the optimizer, only when the number of iterations is reached, the optimization stops.
                  - Don't save files, just Print the result of **50 iteration step** during optimization (e.g., all 50 iterations); Example:`Iteration <n>: MAE = <value> `; and final roughness of each pipes'''

pump_initial_chat = '''Task: Pump Speed Optimization for Cost Reduction

                Input Data:
                - **Hydraulic Network Model**: `../networks/Anytown.inp`
                - **Simulation Function**: `from functions import simulation_objective_pump`
                (Simulates the hydraulic network cost after applying pump speed changes.

                Parameters:
                -----------
                new_speed : list
                    A list of pump speed multipliers applied over the simulation period.
                    - Each value (float) should be between 0.85 and 1.15 (relative to base speed).
                    - The length of this list should match the simulation time steps.

                wn : wntr.network.WaterNetworkModel
                    The water network model to be simulated.

                Returns:
                --------
                float
                    The total energy cost (£) over the simulation period based on the pump energy consumption
                    and time-dependent electricity prices.

                Example:
                --------
                price = simulation_objective_pump([1.0, 1.1, 0.9, ...], wn)

                Objective:
                - Use **`WNTR`** to read `Anytown.inp`**.
                - Implement an **optimization algorithm** to adjust pump speeds for **minimum operating cost**.
                - Ensure pump speed remains **within a valid range (0.85 - 1.15)**.
                - Set `maxiter=50` in the optimizer, only when the number of iterations is reached, the optimization stops.
                - Don't save files, just Print the result of **50 iteration step** during optimization (e.g., all 50 iterations); Example:`Iteration <n>: cost = <value> `'''

if __name__ == "__main__":


    # hydraulic model calibration for net2
    main(calibration_coding_executor,calibration_coding_orchestrating,calibration_initial_chat_net2)
    # hydraulic model calibration for anytown
    main(calibration_coding_executor, calibration_coding_orchestrating, calibration_initial_chat_anytown)
    # pump operation cost optimization for anytown
    main(pump_coding_executor, pump_coding_orchestrating, pump_initial_chat)