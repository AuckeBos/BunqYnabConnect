import os
import subprocess


def _supervisor_dir() -> str:
    """
    Get the supervisor dir
    """
    dir = os.path.dirname(os.path.realpath(__file__))
    config_dir = f"{dir}/../../supervisor"
    return config_dir


def _user() -> str:
    """
    Get the current user
    """
    return subprocess.check_output("whoami").strip().decode("utf-8")


def _create_conf_file():
    """
    Create a config file, based on the config template. The actual file has the <USER>
    variable replaced with the current user
    """
    dir = _supervisor_dir()
    template_file = f"{dir}/supervisord.conf.template"
    with open(template_file, "r") as f:
        template = f.read()
    updated_content = template.replace("<USER>", _user())
    conf_file = f"{dir}/supervisord.conf"
    with open(conf_file, "w") as f:
        f.write(updated_content)


def _add_supervisord_to_cron():
    """
    Add a line to the crontab, which starts supervisord on reboot
    """
    print("Adding supervisor to cron, such that supervisord starts on reboot")
    supervisor_dir = _supervisor_dir()
    supervisord_loc = "$(which supervisord)"
    config_file = f"{supervisor_dir}/supervisord.conf"
    cron_line = f"@reboot {supervisord_loc} -c {config_file} 2>&1"
    user = _user()
    command = f'(crontab -u {user} -l; echo "{cron_line}") | crontab -u {user} -'
    current_cron = subprocess.check_output(f"crontab -u {user} -l", shell=True).decode(
        "utf-8"
    )
    # If the current config_file exists in the cron file, this command is already added
    # once dont't re-add it
    if config_file in current_cron:
        print("Not updating cron, command yet exists in crontab")
    else:
        # First create the actual config file, based on the template
        _create_conf_file()
        # Then add the cron task
        os.system(command)
        print("Cron task added")
    print("Your current cron is as follows:")
    os.system(f"crontab -u {user} -l")


def setup():
    _add_supervisord_to_cron()
