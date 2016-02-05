import jujuresources
from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state
from charmhelpers.core import hookenv
from charms.flume import Flume

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


@when_not('valid.deploymnet')
def verify():
    if not all(map(hookenv.config().get, API_CRED_OPTIONS)):
        hookenv.status_set('blocked', 'Twitter Streaming API credentials must be set')
        return False

    set_state('valid.deploymnet')
    return True

@when('valid.deploymnet')
@when_not('flumeagent.installed')
def install_flume(*args):

    flume = Flume(dist_config())
    if flume.verify_resources():
        hookenv.status_set('maintenance', 'Installing Flume Twitter agent')
        flume.install()
        set_state('flumeagent.installed')


@when('flumeagent.installed')
@when_not('flume-agent.connected')
def waiting_for_flume_connection():
    hookenv.status_set('blocked', 'Waiting for connection to Flume HDFS')


@when('flumeagent.installed','flume-agent.connected')
@when_not('flume-agent.available')
def waiting_for_flume_available(flume):
    hookenv.status_set('blocked', 'Waiting for Flume HDFS to become available')


@when('flumeagent.installed', 'flume-agent.available')
@when_not('flumeagent.started')
def configure_flume(flumehdfs):
    try:
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
    except:
        hookenv.log("Relation with Flume sink not established correctly")


@when('flumeagent.started')
@when_not('flume-agent.available')
def agent_disconnected():
    remove_state('flumeagent.started')
    hookenv.status_set('blocked', 'Waiting for a connection from a Flume agent')

