import pytest
from mission_planner.planner import MissionPlanner
from mission_planner.patterns import grid_pattern

def test_mission_planner():
    waypoints = [(1.0, 1.0, 50.0), (2.0, 2.0, 50.0)]
    planner = MissionPlanner(waypoints)
    
    assert not planner.is_complete()
    assert planner.get_current_target() == (1.0, 1.0, 50.0)
    
    planner.advance()
    assert planner.get_current_target() == (2.0, 2.0, 50.0)
    
    planner.advance()
    assert planner.is_complete()

def test_grid_pattern():
    wps = grid_pattern(48.0, 11.0, 100, 100, 20, 50)
    assert len(wps) > 0
    for wp in wps:
        assert len(wp) == 3
        assert wp[2] == 50
