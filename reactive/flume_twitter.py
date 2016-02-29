from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state
from charms.reactive.helpers import any_file_changed

from charmhelpers.core import hookenv

from charms.layer.flume_base import Flume


API_CRED_OPTIONS = [
    'twitter_access_token',
    'twitter_access_token_secret',
    'twitter_consumer_key',
    'twitter_consumer_secret',
]


@when('flume-base.installed')
def verify_config():
    if all(map(hookenv.config().get, API_CRED_OPTIONS)):
        set_state('flume-twitter.config.valid')
    else:
        remove_state('flume-twitter.config.valid')
        hookenv.status_set('blocked', 'Twitter Streaming API credentials must be set')


@when('flume-base.installed', 'flume-twitter.config.valid')
@when_not('flume-sink.joined')
def waiting_for_flume_connection():
    hookenv.status_set('blocked', 'Waiting for connection to Flume Sink')


@when('flume-base.installed', 'flume-twitter.config.valid', 'flume-sink.joined')
@when_not('flume-sink.ready')
def waiting_for_flume_available(sink):  # pylint: disable=unused-argument
    hookenv.status_set('blocked', 'Waiting for Flume Sink')


@when('flume-base.installed', 'flume-twitter.config.valid', 'flume-sink.ready')
def configure_flume(sink):
    hookenv.status_set('maintenance', 'Configuring Flume')
    flume = Flume()
    flume.configure_flume({'agents': sink.agents()})
    if any_file_changed(flume.config_file):
        flume.restart()
    hookenv.status_set('active', 'Ready')
    set_state('flume-twitter.started')


@when('flume-twitter.started')
@when_not('flume-twitter.config.valid')
def stop_flume():
    flume = Flume()
    flume.stop()
    remove_state('flume-twitter.started')


@when('flume-twitter.started')
@when_not('flume-sink.ready')
def agent_disconnected():
    stop_flume()
