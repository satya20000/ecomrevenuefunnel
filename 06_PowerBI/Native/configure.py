"""Configure the local data folder after cloning. No external dependencies."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
MODEL=next(Path(__file__).parent.glob("*.SemanticModel/model.bim"))
folder=ROOT/"02_Cleaned_Data"
if (folder/"fact_order.csv.gz.part001").exists() and not (folder/"fact_order.csv").exists():
    import runpy
    runpy.run_path(str(ROOT/"04_Python/restore_data.py"),run_name="__main__")
model=json.loads(MODEL.read_text(encoding="utf-8"))
model["model"]["expressions"][0]["expression"]='"'+str(folder).replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
MODEL.write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
print("Configured:",folder)
print("Open the PBIP in Power BI Desktop and click Refresh.")
