import pandas as pd
from pathlib import Path
from bot.config import load_config
from bot.data import load_klines_5m
from bot.study.levels import _level_table, strong_levels
from bot.study.review import plot_big, TFS
from bot.study.flow import load_flow
from bot.study.liquidation import _hourly, load_oi_hourly, liq_levels
cfg=load_config(); df5u,_=load_klines_5m(cfg.data_dir,cfg.symbol)
hb_df=_hourly(load_flow(cfg.data_dir,cfg.symbol))
hb={'t':hb_df['open_time'].to_numpy()}|{c:hb_df[c].to_numpy(float) for c in ('low','high','tp','volume','buy')}
hb['oi']=load_oi_hourly(cfg.data_dir,cfg.symbol,hb_df['open_time'])
t={'entry_time':pd.Timestamp('2026-07-11 16:00'),'exit_time':pd.Timestamp('2026-07-11 23:25'),'entry':1814.11,'risk':14.660043,'direction':1}
t['stop']=t['entry']-t['risk']; t['target']=t['entry']+2*t['risk']
lm=liq_levels(hb,t['entry_time'],'oi')
z=strong_levels(_level_table(df5u), t['entry_time'].tz_localize('UTC'))
for k,(tf,rule) in enumerate(TFS): plot_big(df5u,tf,rule,t,z,Path(f'reports/review/one/h039_{k+1}_{tf}.png'),lm)
