import wntr
import numpy as np

def simulation_objective_calibration(new_roughness: dict, wn:wntr.network.WaterNetworkModel):
    """
    Simulates the hydraulic network pressure after updating pipe roughness values.

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
        ```
    """
    wn.reset_initial_values()
    for pipe_name, pipe in wn.pipes():
        if pipe_name in new_roughness:
            pipe.roughness = new_roughness[pipe_name]
    try:
        sim = wntr.sim.WNTRSimulator(wn)
        results = sim.run_sim()
        pressure = results.node['pressure']
    finally:
        del sim


    return pressure

def simulation_objective_pump(new_speed: list, wn: wntr.network.WaterNetworkModel):
    """
    Simulate the water distribution network with varying pump speeds and compute the total energy cost.

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
    """

    wn.reset_initial_values()
    price = np.array([0.1, 0.1, 0.15, 0.15, 0.2, 0.2, 0.15, 0.1, 0.1])
    if 'speed_pattern' in wn.pattern_name_list:
        wn.get_pattern('speed_pattern').multipliers = new_speed
    else:
        wn.add_pattern('speed_pattern',new_speed)
    pump = wn.get_link('82')
    pump.speed_pattern_name = 'speed_pattern'
    x = wntr.sim.EpanetSimulator(wn)
    result = x.run_sim()
    head = result.node['head']
    flow = result.link['flowrate'].loc[:, ['82']]
    energy = wntr.metrics.pump_energy(flow, head, wn) / 1000 / 3600
    price = np.sum(np.array(energy).flatten() * price)

    return price*3