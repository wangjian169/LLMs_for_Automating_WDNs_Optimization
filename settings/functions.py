import wntr
import numpy as np



def calibration_read_information(original_path,real_path):
    file_path = original_path
    with open(file_path, "r") as file:
        inp_text = file.read()
    wn = wntr.network.WaterNetworkModel(real_path)
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim(version=2.2)
    correct_pressure = results.node['pressure']
    demand = results.node['demand']
    wn2 = wntr.network.WaterNetworkModel(file_path)
    sim2 = wntr.sim.EpanetSimulator(wn2)
    results2 = sim2.run_sim(version=2.2)
    initial_pressure = results2.node['pressure']

    mse = np.mean((correct_pressure - initial_pressure) ** 2)
    mae = np.mean(np.abs(correct_pressure - initial_pressure))

    return inp_text, correct_pressure.iloc[:4], initial_pressure.iloc[:4], demand.iloc[:4], mse, mae

def pump_read_information(file_path):

    price = np.array([0.1, 0.1, 0.15, 0.15, 0.2, 0.2, 0.15, 0.1, 0.1])
    with open(file_path, "r") as file:
        inp_text = file.read()
    wn = wntr.network.WaterNetworkModel(file_path)
    pump = wn.get_link('82')
    pump.speed_pattern_name = 'speed_pattern'
    x = wntr.sim.EpanetSimulator(wn)
    result = x.run_sim()
    head = result.node['head']
    flow = result.link['flowrate'].loc[:, ['82']]
    energy = wntr.metrics.pump_energy(flow, head, wn) / 1000 / 3600
    new_price = np.sum(np.array(energy).flatten() * price)

    return inp_text, energy*3, new_price*3

def simulation_objective_calibration(new_roughness: dict):
    """
        Simulate network pressure based on updated pipe roughness values and calculate error metrics.

        Parameters:
        ----------
        new_roughness: dict
            Dictionary containing updated pipe roughness values.
            Example: {'pipe1': 100, 'pipe2': 90, ...}
            - Keys (str): Pipe names (must match those defined in the network model).
            - Values (float): Roughness values to set for each pipe (must larger than 60 and smaller than 140).

        Returns:
        -------
        tuple:
            A tuple containing three elements:

            calibration_pressure: pandas.Series
                Simulated pressure at each node after applying new roughness values.
                Example: Node names as index, mean pressures as values.

            mse: float
                Mean Squared Error (MSE) between the simulated pressures and actual pressures.
                Lower values indicate better calibration.

            mae: float
                Mean Absolute Error (MAE) between the simulated pressures and actual pressures.
                Lower values indicate better calibration.

        Usage:
        ------
        This function should be called iteratively during the calibration process, with each iteration
        providing incremental adjustments to pipe roughness.

        Note:
        -----
        - The roughness values are cumulative; each call updates the global state of pipe roughness.
        - Ensure 'current_roughness' is initialized using 'get_initial_roughness()' before the first call.

        """


    global current_roughness
    current_roughness.update(new_roughness)

    real_wn = wntr.network.WaterNetworkModel("networks/Anytown.inp")
    real_sim = wntr.sim.EpanetSimulator(real_wn)
    real_results = real_sim.run_sim(version=2.2)
    correct_pressure = real_results.node['pressure']

    calibration_wn = wntr.network.WaterNetworkModel("networks/Anytown_initial.inp")
    for pipe_name, pipe in calibration_wn.pipes():
        if pipe_name in current_roughness:
            pipe.roughness = current_roughness[pipe_name]
    calibration_sim = wntr.sim.EpanetSimulator(calibration_wn)
    calibration_results = calibration_sim.run_sim(version=2.2)
    calibration_pressure = calibration_results.node['pressure']


    mse = np.mean((correct_pressure - calibration_pressure) ** 2)
    mae = np.mean(np.abs(correct_pressure - calibration_pressure))
    return calibration_pressure.iloc[:4], mse, mae

def simulation_objective_pump(new_speed: list) -> tuple:
    """
        Simulate network pressure based on updated pump speed values and calculate pressure fluctuation.

        Parameters:
        -----------
        new_speed : list
            A list of pump speed multipliers to apply over the simulation period.
            Example: [1.0, 1.1, 0.9, ...]
            - Values (float): Should be between 0.85 and 1.15 (base speed multiplier).
            - Each value corresponds to a specific time step in the simulation.

        Returns:
        --------
        tuple:
            A tuple containing two elements:

            1. energy : pandas.DataFrame
               Simulated energy at each node after applying the new pump speed.
               - Rows: Time steps
               - Columns: Junction names
               - Values: energy (in kwh)

            2. price : float
               The calculated operation price a day.

        Example:
        --------
        energy, price = simulation_objective([1.0, 1.1, 0.9, ...])
        """
    price = np.array([0.1, 0.1, 0.15, 0.15, 0.2, 0.2, 0.15, 0.1, 0.1])
    wn = wntr.network.WaterNetworkModel("networks/Anytown.inp")
    if 'speed_pattern' in wn.pattern_name_list:
        wn.get_pattern('speed_pattern').multipliers = new_speed
    else:
        wn.add_pattern('speed_pattern', new_speed)
    pump = wn.get_link('82')
    pump.speed_pattern_name = 'speed_pattern'
    x = wntr.sim.EpanetSimulator(wn)
    result = x.run_sim()
    head = result.node['head']
    flow = result.link['flowrate'].loc[:, ['82']]
    energy = wntr.metrics.pump_energy(flow, head, wn) / 1000 / 3600
    new_price = np.sum(np.array(energy).flatten() * price)

    return energy*3, new_price*3

def get_initial_roughness():
    wn_init = wntr.network.WaterNetworkModel("networks/Anytown_initial.inp")
    roughness = {}
    for pipe_name, pipe in wn_init.pipes():
        roughness[pipe_name] = pipe.roughness
    return roughness

current_roughness = get_initial_roughness()