import io
import logging
import os
from datetime import date, datetime, timezone, timedelta
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import storage

log = logging.getLogger(__name__)


def timer_dec(fn):
    def enchaced_fn(*args, **kwargs):
        start_time = time.time()
        result = fn(*args, *kwargs)
        end_time = time.time()
        print(f'Task time: {end_time - start_time} secondes')
        return result
    
    return enchaced_fn

@timer_dec
def brew_tea(tea_type, steep_time):
    print(f'Brewing {tea_type} tea ...')
    time.sleep(steep_time)
    print('Tea is ready')
    return f'Drink tea by {datetime.now() + timedelta(minutes=30)}'



print(brew_tea('white', 2))
