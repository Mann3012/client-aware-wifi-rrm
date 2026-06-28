import pytest
from src.realistic_simulator.constants import WallMaterial, EnvironmentType
from src.realistic_simulator.environment import WirelessEnvironment, Point, Wall, Obstacle
from src.realistic_simulator.propagation import PropagationEngine

def test_free_space_path_loss():
    env = WirelessEnvironment()
    prop = PropagationEngine(env)
    
    # FSPL at 1m for 5180 MHz should be around 46-47 dB
    fspl_1m = prop.free_space_path_loss(1.0, 5180e6)
    assert 46.0 < fspl_1m < 47.0
    
    # Doubling distance adds ~6 dB
    fspl_2m = prop.free_space_path_loss(2.0, 5180e6)
    assert pytest.approx(fspl_2m - fspl_1m, abs=0.1) == 6.02

def test_log_distance_path_loss():
    env = WirelessEnvironment()
    prop = PropagationEngine(env)
    
    # Path loss exponent 3.0 means doubling distance adds ~9 dB (10 * 3 * log10(2))
    pl_1m = prop.log_distance_path_loss(1.0, 5180e6, 3.0)
    pl_2m = prop.log_distance_path_loss(2.0, 5180e6, 3.0)
    
    assert pytest.approx(pl_2m - pl_1m, abs=0.1) == 9.03

def test_wall_attenuation():
    env = WirelessEnvironment()
    env.walls.append(Wall(Point(5, 0), Point(5, 10), WallMaterial.DRYWALL, attenuation_db=4.0))
    env.walls.append(Wall(Point(7, 0), Point(7, 10), WallMaterial.CONCRETE, attenuation_db=18.0))
    
    prop = PropagationEngine(env)
    
    # Path with no walls
    loss_clear = env.total_wall_attenuation(Point(0, 5), Point(4, 5))
    assert loss_clear == 0.0
    
    # Path crossing drywall
    loss_one = env.total_wall_attenuation(Point(0, 5), Point(6, 5))
    assert loss_one == 4.0
    
    # Path crossing both walls
    loss_both = env.total_wall_attenuation(Point(0, 5), Point(8, 5))
    assert loss_both == 22.0

def test_obstacle_attenuation():
    env = WirelessEnvironment()
    env.obstacles.append(Obstacle(Point(5, 5), 2.0, 2.0, WallMaterial.WOOD))
    prop = PropagationEngine(env)
    
    # Crossing the obstacle
    loss = env.total_wall_attenuation(Point(0, 5), Point(10, 5))
    assert loss > 0.0
