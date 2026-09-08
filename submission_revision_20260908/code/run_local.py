"""Process-local workaround for a stalled Windows WMI service during import.

No system files/settings change. Python's standard fallback reads the native
Windows version when its optional WMI query raises OSError. Analysis unchanged.
"""
import platform,runpy,sys,os
def no_wmi(*args,**kwargs):
    raise OSError('Skip unresponsive WMI in this analysis process')
if os.name=='nt':platform._wmi_query=no_wmi
script=sys.argv[1];sys.argv=sys.argv[1:]
sys.path.insert(0,os.path.dirname(os.path.abspath(script)))
runpy.run_path(script,run_name='__main__')
