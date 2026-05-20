                                                                                       
  ---                                                                                                                                   
  Option 1 — Rolling RAD lines (simplest)                                                                                               
                                                                                                                                        
  Plot the 5/10/20-day rolling averages as lines on a separate pane. One line per metric. Zero line as the signal threshold.            
                                                                                                                                        
  +1.5% ·····················╭──  Sess 5d                   
                        ╭────╯    Sess 10d                                                                                              
   0%   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ zero line                                                                                             
        ╮          ╭──╯            Sess 20d                                                                                             
  -1.5% ╰──────────╯                                                                                                                    
        Mar/10  Mar/17  Mar/24  Apr/01                                                                                                  
                                                                                                                                        
  Clean signal: when all three lines cross above zero = regime turning bullish. Already computed — just needs plot() calls added.       
                                                                                                                                        
  ---                                                                                                                                   
  Option 2 — Period contribution bars per day               
                                                                                                                                        
  Each day rendered as 5 stacked color segments showing how each period contributed. Plotted at the 16:00 bar.
                                                                                                                                        
       │  +7.87│             ← Gap (gray)                   
   +   │  +0.42│     ← P1 (orange, Amateur)                                                                                             
       │  ──── │ +10.84 Total                                                                                                           
  ─────┼────── ┼ ─────────── zero                                                                                                       
       │  -3.74│             ← P2 (blue)                                                                                                
   -   │  +5.56│             ← P3 (teal, Middle)                                                                                        
       │  +0.75│             ← P4 (purple, Smart)                                                                                       
          3/31                                                                                                                          
                                                                                                                                        
  Each bar tells the story of the day structurally. You immediately see if the day was gap-driven vs session-driven.                    
                                                                                                                                        
  ---                                                                                                                                   
  Option 3 — Cumulative period lines (most analytical)      
                                                      
  One line per period accumulating dollar contribution over time. Shows which "player" has been winning the multi-week battle.
                                                                                                                                        
  +30  ╭── Gap (cumulative)
  +20  │  ╭── Smart P2+P4                                                                                                               
  +10  │  │                                                                                                                             
    0  ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌                                                                                                             
  -10        ╰── Middle P3                                                                                                              
  -20  ╰───────── Amateur P1                                                                                                            
       Mar/10       Apr/01                                                                                                              
                                                                                                                                        
  This is the most powerful view — you can see for example "Smart money has been accumulating +20pts since mid-March while Amateur is   
  down -20pts" = classic institutional accumulation pattern.                                                                            
                                                                                                                                        
  ---                                                       
  Which is most feasible in Pine Script?
                                        
  ┌─────────────────────┬─────────────┬──────────────────────────────────────────────────┐
  │       Option        │ Feasibility │                      Notes                       │                                              
  ├─────────────────────┼─────────────┼──────────────────────────────────────────────────┤
  │ Rolling RAD lines   │ Easy        │ Values already computed, just add plot()         │                                              
  ├─────────────────────┼─────────────┼──────────────────────────────────────────────────┤
  │ Period bars per day │ Medium      │ Needs plot() at 16:00 bar, one series per period │
  ├─────────────────────┼─────────────┼──────────────────────────────────────────────────┤                                              
  │ Cumulative lines    │ Medium      │ Track running sum per period at each 16:00 bar   │
  └─────────────────────┴─────────────┴──────────────────────────────────────────────────┘                                              
                                                            
  All three are doable. Option 1 is a 10-line addition. Options 2 and 3 require tracking values bar-by-bar (not just in arrays at       
  barstate.islast) so the series is plotable historically.  
                                                                                                                                        
  Which direction interests you most?        
