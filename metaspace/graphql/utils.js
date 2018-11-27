const slack = require('node-slack'),
  jsondiffpatch = require('jsondiffpatch'),
  winston = require('winston'),
  moment = require('moment'),
  { PubSub } = require('graphql-subscriptions'),
  fetch = require('node-fetch');

const config = require('config');

function metadataChangeSlackNotify(user, datasetId, oldMetadata, newMetadata) {
  const delta = jsondiffpatch.diff(oldMetadata, newMetadata),
    diff = jsondiffpatch.formatters.jsonpatch.format(delta);

  const slackConn = config.slack.webhook_url ? new slack(config.slack.webhook_url): null;
  if (slackConn) {
    let msg = slackConn.send({
      text: `${user} edited metadata of dataset (id: ${datasetId})` +
      "\nDifferences:\n" + JSON.stringify(diff, null, 2),
      channel: config.slack.channel
    });
  }
}

function metadataUpdateFailedSlackNotify(user, datasetId, e_msg) {
  const slackConn = config.slack.webhook_url ? new slack(config.slack.webhook_url): null;
  if (slackConn) {
    let msg = slackConn.send({
      text: `${user} tried to edit metadata (ds_id=${datasetId})\nError: ${e_msg}`,
      channel: config.slack.channel
    });
  }
}

const logger = new (winston.Logger)({
  transports: [
    new (winston.transports.Console)({
      level: config.log.level,
      timestamp: function() {
        return moment().format('YYYY-MM-DD HH:mm:ss,SSS');
      },
      // formatter: function(options) {
      //   // TODO Lachlan: This custom formatter logs an empty string when given an error
      //   // Copy the default formatter's behavior for when options.message is empty
      //   // Return string will be passed to logger.
      //   return options.timestamp() +' - '+ options.level.toUpperCase() +' - '+ (options.message ? options.message : '') +
      //     (options.meta && Object.keys(options.meta).length ? '\n\t'+ JSON.stringify(options.meta) : '' );
      // }
    })
  ]
});

const pubsub = new PubSub();

function canUserViewPgDataset(dataset, user) {
  return dataset.is_public
    || (user != null && user.role === 'admin')
    || (user != null && user.email != null && user.email !== ''
      && dataset.metadata.Submitted_By.Submitter.Email === user.email);
}

const deprecatedMolDBs = new Set(['HMDB', 'ChEBI', 'LIPID_MAPS', 'SwissLipids', 'COTTON_HMDB']);

async function fetchMolecularDatabases() {
  const host = config.services.moldb_service_host,
    resp = await fetch(`http://${host}/v1/databases`),
    body = await resp.json();
  return body['data'];
}

async function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export {
  metadataChangeSlackNotify,
  metadataUpdateFailedSlackNotify,
  canUserViewPgDataset,
  fetchMolecularDatabases,
  deprecatedMolDBs,
  wait,
  config,
  logger,
  pubsub,
};
