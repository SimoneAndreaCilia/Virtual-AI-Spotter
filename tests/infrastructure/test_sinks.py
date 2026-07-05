import numpy as np
import pytest
from src.infrastructure.sinks import DequeOutputSink

def test_deque_output_sink_drop_oldest():
    sink = DequeOutputSink(maxlen=2)
    
    # Emit 3 items
    sink.emit(np.zeros((10, 10)), '{"frame": 1}')
    sink.emit(np.zeros((10, 10)), '{"frame": 2}')
    sink.emit(np.zeros((10, 10)), '{"frame": 3}')
    
    # We should get frame 2 and frame 3, frame 1 should be dropped
    item1 = sink.get_latest()
    assert item1 is not None
    assert item1[1] == '{"frame": 2}'
    
    item2 = sink.get_latest()
    assert item2 is not None
    assert item2[1] == '{"frame": 3}'
    
    # Should be empty now
    assert sink.get_latest() is None
