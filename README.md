## Overview

Flume is a distributed, reliable, and available service for efficiently
collecting, aggregating, and moving large amounts of log data. It has a simple
and flexible architecture based on streaming data flows. It is robust and fault
tolerant with tunable reliability mechanisms and many failover and recovery
mechanisms. It uses a simple extensible data model that allows for online
analytic application. Learn more at [flume.apache.org](http://flume.apache.org).

This charm provides a Flume agent designed to process tweets from the Twitter
Streaming API and send them to the `apache-flume-hdfs` agent for storage in
the shared filesystem (HDFS) of a connected Hadoop cluster. This leverages the
TwitterSource jar packaged with Flume. Learn more about the
[1% firehose](https://flume.apache.org/FlumeUserGuide.html#twitter-1-firehose-source-experimental).


## Prerequisites

The Twitter Streaming API requires developer credentials. You'll need to
configure those for this charm. Find your credentials (or create an account
if needed) [here](https://apps.twitter.com/).

Create a `secret.yaml` file with your Twitter developer credentials:

    flume-twitter:
        twitter_access_token: 'YOUR_TOKEN'
        twitter_access_token_secret: 'YOUR_TOKEN_SECRET'
        twitter_consumer_key: 'YOUR_CONSUMER_KEY'
        twitter_consumer_secret: 'YOUR_CONSUMER_SECRET'


## Usage
This charm is uses the Hadoob base layer and the HDFS interface to pull its dependencies
and act as a client to a Hadoop namenode:

You may manually deploy the recommended environment as follows:

    juju deploy apache-hadoop-datanode datanode
    juju deploy apache-hadoop-namenode namenode
    juju deploy apache-hadoop-nodemanager nodemgr
    juju deploy apache-hadoop-resourcemanager resourcemgr
    juju deploy apache-hadoop-plugin plugin

    juju add-relation namenode datanode
    juju add-relation resourcemgr nodemgr
    juju add-relation resourcemgr namenode
    juju add-relation plugin resourcemgr
    juju add-relation plugin namenode

Deploy Flume hdfs:

    juju deploy apache-flume-hdfs flume-hdfs
    juju add-relation flume-hdfs plugin

Now that the base environment has been deployed (either via quickstart or
manually), you are ready to add the `apache-flume-twitter` charm and
relate it to the `flume-hdfs` agent:

    juju deploy apache-flume-twitter flume-twitter --config=secret.yaml
    juju add-relation flume-twitter flume-hdfs

Make sure you name the service `flume-twitter` so that it matches the first line of `secret.yaml`.

That's it! Once the Flume agents start, tweets will start flowing into
HDFS via the `flume-twitter` and `flume-hdfs` charms. Flume may include
multiple events in each file written to HDFS. This is configurable with various
options on the `flume-hdfs` charm. See descriptions of the `roll_*` options on
the [apache-flume-hdfs](https://jujucharms.com/apache-flume-hdfs/) charm store
page for more details.

Flume will write files to HDFS in the following location:
`/user/flume/<event_dir>/<yyyy-mm-dd>/FlumeData.<id>`. The `<event_dir>`
subdirectory is configurable and set to `flume-twitter` by default for this
charm.

## Test the deployment

To verify this charm is working as intended, SSH to the `flume-hdfs` unit and
locate an event:

    juju ssh flume-hdfs/0
    hdfs dfs -ls /user/flume/<event_dir>               # <-- find a date
    hdfs dfs -ls /user/flume/<event_dir>/<yyyy-mm-dd>  # <-- find an event

Since our tweets are serialized in `avro` format, you'll need to copy the file
locally and use the `dfs -text` command to view it:

    hdfs dfs -copyToLocal /user/flume/<event_dir>/<yyyy-mm-dd>/FlumeData.<id>.avro /home/ubuntu/myFile.txt
    hdfs dfs -text file:///home/ubuntu/myFile.txt

You may not recognize the body of the tweet if it's not in a language you
understand (remember, this is a 1% firehose from tweets all over the world).
You may have to try a few different events before you find a tweet worth
reading. Happy hunting!


## Contact Information

- <bigdata@lists.ubuntu.com>


## Help

- [Apache Flume home page](http://flume.apache.org/)
- [Apache Flume bug tracker](https://issues.apache.org/jira/browse/flume)
- [Apache Flume mailing lists](https://flume.apache.org/mailinglists.html)
- `#juju` on `irc.freenode.net`
