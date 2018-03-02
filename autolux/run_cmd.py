import time
import shlex, subprocess
import opts

def run_cmd(cmd, bg=False):
  args = shlex.split(cmd)
  start = int(round(time.time() * 1000))
  ret = ""
  if not bg:
    ret = subprocess.check_output(args)
  else:
    subprocess.Popen(args)

  end = int(round(time.time() * 1000))
  if opts.VERBOSE and end - start > 50:
    print "TIME:", end - start, "CMD", cmd.split()[0]
  return ret

