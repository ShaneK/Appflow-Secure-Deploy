import json
import uasyncio
import urequests

from env.env import Environment


async def get_builds():
    print("Getting builds...")
    operation_name = "BuildsList"
    operation_query = """
query BuildsList($appId: String!, $first: Int, $last: Int, $after: String, $before: String, $state: JobState, $platform: Platform, $deployable: Boolean) {
    app(id: $appId) {
        builds(
            first: $first
            last: $last
            after: $after
            before: $before
            state: $state
            platform: $platform
            deployable: $deployable
        ) {
            totalCount
            pageInfo {
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
            edges {
                cursor
                node {
                    __typename
                    ...BuildListFields
                    ...DeployBuildListFields
                    ...PackageBuildListFields
                }
            }
        }
    }
}

fragment BuildListFields on Build {
    __typename
    number
    jobId
    uuid
    app {
        id
    }
}

fragment DeployBuildListFields on DeployBuild {
    id
    jobId
    callerId
    uuid
    app {
        id
    }
}

fragment PackageBuildListFields on PackageBuild {
  id
  number
  uuid
  app {
    id
  }
}
    """
    payload = {
        "operationName": operation_name,
        "query": operation_query,
        "variables": {
            "appId": Environment.APP_ID,
            "first": 1
        }
    }
    response = urequests.post(Environment.GRAPHQL_URL, json=payload, headers={
        "Authorization": "Bearer " + Environment.APPFLOW_TOKEN
    }).json()
    return response["data"]["app"]["builds"]["edges"]


async def get_channels():
    get_channels_query_name = "GetChannels"
    get_channels_query = """
query GetChannels($appId: String!){
  app(id:$appId) {
    channels {
      edges {
        node {
          name
          build {
            id
            uuid
          }
        }
      }
    }
  }
} 
   """
    payload = {
        "operationName": get_channels_query_name,
        "query": get_channels_query,
        "variables": {
            "appId": Environment.APP_ID,
        }
    }
    response = urequests.post(Environment.GRAPHQL_URL, json=payload, headers={
        "Authorization": "Bearer " + Environment.APPFLOW_TOKEN
    }).json()
    return response["data"]["app"]["channels"]["edges"]

async def deploy_build(build_id):
    try:
        deploy_url = f"{Environment.API_URL}/apps/{Environment.APP_ID}/channels/{Environment.PRODUCTION_CHANNEL_ID}"
        print(f"Deploy URL: {deploy_url}")
        print(f"Snapshot ID: {build_id}")
        print(f"Auth token: {Environment.APPFLOW_TOKEN}")
        urequests.patch(deploy_url, json={
            "snapshot_id": build_id
        }, headers={
            "Authorization": "Bearer " + Environment.APPFLOW_TOKEN
        }).json()
    except Exception as e:
        print("Error deploying build:")
        print(e)
