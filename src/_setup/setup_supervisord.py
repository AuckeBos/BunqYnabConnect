import os
import subprocess


def _add_supervisord_to_cron():
    """
    Add a line to the crontab, which starts supervisord on reboot
    """
    print("Adding supervisor to cron, such that supervisord starts on reboot")
    dir = os.path.dirname(os.path.realpath(__file__))
    supervisord_loc = "$(poetry run which supervisord)"
    config_dir = f"{dir}../../supervisor/supervisord.conf"
    cron_line = f"@reboot {supervisord_loc} -c {config_dir} 2>&1"
    user = subprocess.check_output("whoami").strip().decode("utf-8")
    command = f'(crontab -u {user} -l; echo "{cron_line}") | crontab -u {user} -'
    current_cron = subprocess.check_output(f"crontab -u {user} -l", shell=True).decode(
        "utf-8"
    )
    # If the current dir exists in the cron file, this command is already added once,
    # dont't re-add it
    if config_dir in current_cron:
        print("Not updating cron, command yet exists in crontab")
    else:
        os.system(command)
        print("Cron task added")
    print("Your current cron is as follows:")
    os.system(f"crontab -u {user} -l")


def setup():
    _add_supervisord_to_cron()
