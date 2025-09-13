magaye:irdpassword

 python - <<'PY'
import inspect, rest_framework, shutil, pathlib, sys
src = pathlib.Path(inspect.getfile(rest_framework)).with_name("templates") / "rest_framework" / "base.html"
dst = pathlib.Path("geosoil/templates/rest_framework/base.html")
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(src, dst)
print("Template copié :", dst)
PY