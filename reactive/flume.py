import jujuresources
from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state, is_state
from charmhelpers.core import hookenv
from subprocess import check_call
from glob import glob

API_CRED_OPTIONS = [
    'twitter_access_token',
    'twitter_access_token_secret',
    'twitter_consumer_key',
    'twitter_consumer_secret',
]

def dist_config():
    from jujubigdata.utils import DistConfig  # no available until after bootstrap

    if not getattr(dist_config, 'value', None):
        flume_reqs = ['packages', 'groups', 'users', 'dirs']
        dist_config.value = DistConfig(filename='dist.yaml', required_keys=flume_reqs)
    return dist_config.value


@when_not('bootstrapped')
def bootstrap():    
    if not all(map(hookenv.config().get, API_CRED_OPTIONS)):
        hookenv.status_set('blocked', 'Twitter Streaming API credentials must be set')
        return False

    hookenv.status_set('maintenance', 'Installing base resources')
    check_call(['apt-get', 'install', '-yq', 'python-pip', 'bzr'])
    archives = glob('resources/python/*')
    check_call(['pip', 'install'] + archives)

    """
    Install required resources defined in resources.yaml
    """
    mirror_url = jujuresources.config_get('resources_mirror')
    if not jujuresources.fetch(mirror_url=mirror_url):
        missing = jujuresources.invalid()
        hookenv.status_set('blocked', 'Unable to fetch required resource%s: %s' % (
            's' if len(missing) > 1 else '',
            ', '.join(missing),
        ))
        return False

    set_state('bootstrapped')
    return True

@when('bootstrapped')
@when_not('flumeagent.installed')
def install_flume(*args):
    from charms.flume import Flume  # in lib/charms; not available until after bootstrap

    flume = Flume(dist_config())
    if flume.verify_resources():
        hookenv.status_set('maintenance', 'Installing Flume Twitter agent')
        flume.install()
        set_state('flumeagent.installed')


@when('flumeagent.installed')
@when_not('flume-agent.available')
def waiting_for_flume_connection():
    hookenv.status_set('blocked', 'Waiting for connection to Flume HDFS')


@when('flumeagent.installed', 'flume-agent.available')
@when_not('flumeagent.started')
def configure_flume(flumehdfs):
    from charms.flume import Flume  # in lib/charms; not available until after bootstrap

    port = flumehdfs.get_flume_port()
    ip = flumehdfs.get_flume_ip()
    protocol = flumehdfs.get_flume_protocol()
    flumehdfsinfo = {'port': port, 'private-address': ip, 'protocol': protocol}
    hookenv.log("Connecting to Flume HDFS at {}:{} using {}".format(port, ip, protocol))
    hookenv.status_set('maintenance', 'Setting up Flume')
    flume = Flume(dist_config())
    flume.configure_flume(flumehdfsinfo)
    flume.restart()
    hookenv.status_set('active', 'Ready')
    set_state('flumeagent.started')


@when('flumeagent.started')
@when_not('flume-agent.available')
def agent_disconnected():
    remove_state('flumeagent.started')
    hookenv.status_set('blocked', 'Waiting for a connection from a Flume agent')

