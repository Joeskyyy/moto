from __future__ import unicode_literals

import json
import os
import random
import uuid

import boto3
# noinspection PyUnresolvedReferences
import sure  # noqa
from botocore.exceptions import ClientError
from jose import jws
from nose.tools import assert_raises

from moto import mock_cognitoidp


@mock_cognitoidp
def test_create_user_pool():
    conn = boto3.client("cognito-idp", "us-west-2")

    name = str(uuid.uuid4())
    value = str(uuid.uuid4())
    result = conn.create_user_pool(
        PoolName=name,
        LambdaConfig={
            "PreSignUp": value
        }
    )

    result["UserPool"]["Id"].should_not.be.none
    result["UserPool"]["Id"].should.match(r'[\w-]+_[0-9a-zA-Z]+')
    result["UserPool"]["Name"].should.equal(name)
    result["UserPool"]["LambdaConfig"]["PreSignUp"].should.equal(value)


@mock_cognitoidp
def test_list_user_pools():
    conn = boto3.client("cognito-idp", "us-west-2")

    name = str(uuid.uuid4())
    conn.create_user_pool(PoolName=name)
    result = conn.list_user_pools(MaxResults=10)
    result["UserPools"].should.have.length_of(1)
    result["UserPools"][0]["Name"].should.equal(name)


@mock_cognitoidp
def test_list_user_pools_returns_max_items():
    conn = boto3.client("cognito-idp", "us-west-2")

    # Given 10 user pools
    pool_count = 10
    for i in range(pool_count):
        conn.create_user_pool(PoolName=str(uuid.uuid4()))

    max_results = 5
    result = conn.list_user_pools(MaxResults=max_results)
    result["UserPools"].should.have.length_of(max_results)
    result.should.have.key("NextToken")


@mock_cognitoidp
def test_list_user_pools_returns_next_tokens():
    conn = boto3.client("cognito-idp", "us-west-2")

    # Given 10 user pool clients
    pool_count = 10
    for i in range(pool_count):
        conn.create_user_pool(PoolName=str(uuid.uuid4()))

    max_results = 5
    result = conn.list_user_pools(MaxResults=max_results)
    result["UserPools"].should.have.length_of(max_results)
    result.should.have.key("NextToken")

    next_token = result["NextToken"]
    result_2 = conn.list_user_pools(MaxResults=max_results, NextToken=next_token)
    result_2["UserPools"].should.have.length_of(max_results)
    result_2.shouldnt.have.key("NextToken")


@mock_cognitoidp
def test_list_user_pools_when_max_items_more_than_total_items():
    conn = boto3.client("cognito-idp", "us-west-2")

    # Given 10 user pool clients
    pool_count = 10
    for i in range(pool_count):
        conn.create_user_pool(PoolName=str(uuid.uuid4()))

    max_results = pool_count + 5
    result = conn.list_user_pools(MaxResults=max_results)
    result["UserPools"].should.have.length_of(pool_count)
    result.shouldnt.have.key("NextToken")


@mock_cognitoidp
def test_describe_user_pool():
    conn = boto3.client("cognito-idp", "us-west-2")

    name = str(uuid.uuid4())
    value = str(uuid.uuid4())
    user_pool_details = conn.create_user_pool(
        PoolName=name,
        LambdaConfig={
            "PreSignUp": value
        }
    )

    result = conn.describe_user_pool(UserPoolId=user_pool_details["UserPool"]["Id"])
    result["UserPool"]["Name"].should.equal(name)
    result["UserPool"]["LambdaConfig"]["PreSignUp"].should.equal(value)


@mock_cognitoidp
def test_delete_user_pool():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.list_user_pools(MaxResults=10)["UserPools"].should.have.length_of(1)
    conn.delete_user_pool(UserPoolId=user_pool_id)
    conn.list_user_pools(MaxResults=10)["UserPools"].should.have.length_of(0)


@mock_cognitoidp
def test_create_user_pool_domain():
    conn = boto3.client("cognito-idp", "us-west-2")

    domain = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    result = conn.create_user_pool_domain(UserPoolId=user_pool_id, Domain=domain)
    result["ResponseMetadata"]["HTTPStatusCode"].should.equal(200)


@mock_cognitoidp
def test_describe_user_pool_domain():
    conn = boto3.client("cognito-idp", "us-west-2")

    domain = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.create_user_pool_domain(UserPoolId=user_pool_id, Domain=domain)
    result = conn.describe_user_pool_domain(Domain=domain)
    result["DomainDescription"]["Domain"].should.equal(domain)
    result["DomainDescription"]["UserPoolId"].should.equal(user_pool_id)
    result["DomainDescription"]["AWSAccountId"].should_not.be.none


@mock_cognitoidp
def test_delete_user_pool_domain():
    conn = boto3.client("cognito-idp", "us-west-2")

    domain = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.create_user_pool_domain(UserPoolId=user_pool_id, Domain=domain)
    result = conn.delete_user_pool_domain(UserPoolId=user_pool_id, Domain=domain)
    result["ResponseMetadata"]["HTTPStatusCode"].should.equal(200)
    result = conn.describe_user_pool_domain(Domain=domain)
    # This is a surprising behavior of the real service: describing a missing domain comes
    # back with status 200 and a DomainDescription of {}
    result["ResponseMetadata"]["HTTPStatusCode"].should.equal(200)
    result["DomainDescription"].keys().should.have.length_of(0)


@mock_cognitoidp
def test_create_user_pool_client():
    conn = boto3.client("cognito-idp", "us-west-2")

    client_name = str(uuid.uuid4())
    value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    result = conn.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=client_name,
        CallbackURLs=[value],
    )

    result["UserPoolClient"]["UserPoolId"].should.equal(user_pool_id)
    result["UserPoolClient"]["ClientId"].should_not.be.none
    result["UserPoolClient"]["ClientName"].should.equal(client_name)
    result["UserPoolClient"]["CallbackURLs"].should.have.length_of(1)
    result["UserPoolClient"]["CallbackURLs"][0].should.equal(value)


@mock_cognitoidp
def test_list_user_pool_clients():
    conn = boto3.client("cognito-idp", "us-west-2")

    client_name = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.create_user_pool_client(UserPoolId=user_pool_id, ClientName=client_name)
    result = conn.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=10)
    result["UserPoolClients"].should.have.length_of(1)
    result["UserPoolClients"][0]["ClientName"].should.equal(client_name)


@mock_cognitoidp
def test_list_user_pool_clients_returns_max_items():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 user pool clients
    client_count = 10
    for i in range(client_count):
        client_name = str(uuid.uuid4())
        conn.create_user_pool_client(UserPoolId=user_pool_id,
                                     ClientName=client_name)
    max_results = 5
    result = conn.list_user_pool_clients(UserPoolId=user_pool_id,
                                         MaxResults=max_results)
    result["UserPoolClients"].should.have.length_of(max_results)
    result.should.have.key("NextToken")


@mock_cognitoidp
def test_list_user_pool_clients_returns_next_tokens():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 user pool clients
    client_count = 10
    for i in range(client_count):
        client_name = str(uuid.uuid4())
        conn.create_user_pool_client(UserPoolId=user_pool_id,
                                     ClientName=client_name)
    max_results = 5
    result = conn.list_user_pool_clients(UserPoolId=user_pool_id,
                                         MaxResults=max_results)
    result["UserPoolClients"].should.have.length_of(max_results)
    result.should.have.key("NextToken")

    next_token = result["NextToken"]
    result_2 = conn.list_user_pool_clients(UserPoolId=user_pool_id,
                                           MaxResults=max_results,
                                           NextToken=next_token)
    result_2["UserPoolClients"].should.have.length_of(max_results)
    result_2.shouldnt.have.key("NextToken")


@mock_cognitoidp
def test_list_user_pool_clients_when_max_items_more_than_total_items():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 user pool clients
    client_count = 10
    for i in range(client_count):
        client_name = str(uuid.uuid4())
        conn.create_user_pool_client(UserPoolId=user_pool_id,
                                     ClientName=client_name)
    max_results = client_count + 5
    result = conn.list_user_pool_clients(UserPoolId=user_pool_id,
                                         MaxResults=max_results)
    result["UserPoolClients"].should.have.length_of(client_count)
    result.shouldnt.have.key("NextToken")


@mock_cognitoidp
def test_describe_user_pool_client():
    conn = boto3.client("cognito-idp", "us-west-2")

    client_name = str(uuid.uuid4())
    value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    client_details = conn.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=client_name,
        CallbackURLs=[value],
    )

    result = conn.describe_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=client_details["UserPoolClient"]["ClientId"],
    )

    result["UserPoolClient"]["ClientName"].should.equal(client_name)
    result["UserPoolClient"]["CallbackURLs"].should.have.length_of(1)
    result["UserPoolClient"]["CallbackURLs"][0].should.equal(value)


@mock_cognitoidp
def test_update_user_pool_client():
    conn = boto3.client("cognito-idp", "us-west-2")

    old_client_name = str(uuid.uuid4())
    new_client_name = str(uuid.uuid4())
    old_value = str(uuid.uuid4())
    new_value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    client_details = conn.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=old_client_name,
        CallbackURLs=[old_value],
    )

    result = conn.update_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=client_details["UserPoolClient"]["ClientId"],
        ClientName=new_client_name,
        CallbackURLs=[new_value],
    )

    result["UserPoolClient"]["ClientName"].should.equal(new_client_name)
    result["UserPoolClient"]["CallbackURLs"].should.have.length_of(1)
    result["UserPoolClient"]["CallbackURLs"][0].should.equal(new_value)


@mock_cognitoidp
def test_delete_user_pool_client():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    client_details = conn.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=str(uuid.uuid4()),
    )

    conn.delete_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=client_details["UserPoolClient"]["ClientId"],
    )

    caught = False
    try:
        conn.describe_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_details["UserPoolClient"]["ClientId"],
        )
    except conn.exceptions.ResourceNotFoundException:
        caught = True

    caught.should.be.true


@mock_cognitoidp
def test_create_identity_provider():
    conn = boto3.client("cognito-idp", "us-west-2")

    provider_name = str(uuid.uuid4())
    provider_type = "Facebook"
    value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    result = conn.create_identity_provider(
        UserPoolId=user_pool_id,
        ProviderName=provider_name,
        ProviderType=provider_type,
        ProviderDetails={
            "thing": value
        },
    )

    result["IdentityProvider"]["UserPoolId"].should.equal(user_pool_id)
    result["IdentityProvider"]["ProviderName"].should.equal(provider_name)
    result["IdentityProvider"]["ProviderType"].should.equal(provider_type)
    result["IdentityProvider"]["ProviderDetails"]["thing"].should.equal(value)


@mock_cognitoidp
def test_list_identity_providers():
    conn = boto3.client("cognito-idp", "us-west-2")

    provider_name = str(uuid.uuid4())
    provider_type = "Facebook"
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.create_identity_provider(
        UserPoolId=user_pool_id,
        ProviderName=provider_name,
        ProviderType=provider_type,
        ProviderDetails={},
    )

    result = conn.list_identity_providers(
        UserPoolId=user_pool_id,
        MaxResults=10,
    )

    result["Providers"].should.have.length_of(1)
    result["Providers"][0]["ProviderName"].should.equal(provider_name)
    result["Providers"][0]["ProviderType"].should.equal(provider_type)


@mock_cognitoidp
def test_list_identity_providers_returns_max_items():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 identity providers linked to a user pool
    identity_provider_count = 10
    for i in range(identity_provider_count):
        provider_name = str(uuid.uuid4())
        provider_type = "Facebook"
        conn.create_identity_provider(
            UserPoolId=user_pool_id,
            ProviderName=provider_name,
            ProviderType=provider_type,
            ProviderDetails={},
        )

    max_results = 5
    result = conn.list_identity_providers(UserPoolId=user_pool_id,
                                          MaxResults=max_results)
    result["Providers"].should.have.length_of(max_results)
    result.should.have.key("NextToken")


@mock_cognitoidp
def test_list_identity_providers_returns_next_tokens():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 identity providers linked to a user pool
    identity_provider_count = 10
    for i in range(identity_provider_count):
        provider_name = str(uuid.uuid4())
        provider_type = "Facebook"
        conn.create_identity_provider(
            UserPoolId=user_pool_id,
            ProviderName=provider_name,
            ProviderType=provider_type,
            ProviderDetails={},
        )

    max_results = 5
    result = conn.list_identity_providers(UserPoolId=user_pool_id, MaxResults=max_results)
    result["Providers"].should.have.length_of(max_results)
    result.should.have.key("NextToken")

    next_token = result["NextToken"]
    result_2 = conn.list_identity_providers(UserPoolId=user_pool_id,
                                           MaxResults=max_results,
                                           NextToken=next_token)
    result_2["Providers"].should.have.length_of(max_results)
    result_2.shouldnt.have.key("NextToken")


@mock_cognitoidp
def test_list_identity_providers_when_max_items_more_than_total_items():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 identity providers linked to a user pool
    identity_provider_count = 10
    for i in range(identity_provider_count):
        provider_name = str(uuid.uuid4())
        provider_type = "Facebook"
        conn.create_identity_provider(
            UserPoolId=user_pool_id,
            ProviderName=provider_name,
            ProviderType=provider_type,
            ProviderDetails={},
        )

    max_results = identity_provider_count + 5
    result = conn.list_identity_providers(UserPoolId=user_pool_id, MaxResults=max_results)
    result["Providers"].should.have.length_of(identity_provider_count)
    result.shouldnt.have.key("NextToken")


@mock_cognitoidp
def test_describe_identity_providers():
    conn = boto3.client("cognito-idp", "us-west-2")

    provider_name = str(uuid.uuid4())
    provider_type = "Facebook"
    value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.create_identity_provider(
        UserPoolId=user_pool_id,
        ProviderName=provider_name,
        ProviderType=provider_type,
        ProviderDetails={
            "thing": value
        },
    )

    result = conn.describe_identity_provider(
        UserPoolId=user_pool_id,
        ProviderName=provider_name,
    )

    result["IdentityProvider"]["UserPoolId"].should.equal(user_pool_id)
    result["IdentityProvider"]["ProviderName"].should.equal(provider_name)
    result["IdentityProvider"]["ProviderType"].should.equal(provider_type)
    result["IdentityProvider"]["ProviderDetails"]["thing"].should.equal(value)


@mock_cognitoidp
def test_delete_identity_providers():
    conn = boto3.client("cognito-idp", "us-west-2")

    provider_name = str(uuid.uuid4())
    provider_type = "Facebook"
    value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.create_identity_provider(
        UserPoolId=user_pool_id,
        ProviderName=provider_name,
        ProviderType=provider_type,
        ProviderDetails={
            "thing": value
        },
    )

    conn.delete_identity_provider(UserPoolId=user_pool_id, ProviderName=provider_name)

    caught = False
    try:
        conn.describe_identity_provider(
            UserPoolId=user_pool_id,
            ProviderName=provider_name,
        )
    except conn.exceptions.ResourceNotFoundException:
        caught = True

    caught.should.be.true


@mock_cognitoidp
def test_create_group():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    description = str(uuid.uuid4())
    role_arn = "arn:aws:iam:::role/my-iam-role"
    precedence = random.randint(0, 100000)

    result = conn.create_group(
        GroupName=group_name,
        UserPoolId=user_pool_id,
        Description=description,
        RoleArn=role_arn,
        Precedence=precedence,
    )

    result["Group"]["GroupName"].should.equal(group_name)
    result["Group"]["UserPoolId"].should.equal(user_pool_id)
    result["Group"]["Description"].should.equal(description)
    result["Group"]["RoleArn"].should.equal(role_arn)
    result["Group"]["Precedence"].should.equal(precedence)
    result["Group"]["LastModifiedDate"].should.be.a("datetime.datetime")
    result["Group"]["CreationDate"].should.be.a("datetime.datetime")


@mock_cognitoidp
def test_create_group_with_duplicate_name_raises_error():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())

    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    with assert_raises(ClientError) as cm:
        conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)
    cm.exception.operation_name.should.equal('CreateGroup')
    cm.exception.response['Error']['Code'].should.equal('GroupExistsException')
    cm.exception.response['ResponseMetadata']['HTTPStatusCode'].should.equal(400)


@mock_cognitoidp
def test_get_group():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    result = conn.get_group(GroupName=group_name, UserPoolId=user_pool_id)

    result["Group"]["GroupName"].should.equal(group_name)
    result["Group"]["UserPoolId"].should.equal(user_pool_id)
    result["Group"]["LastModifiedDate"].should.be.a("datetime.datetime")
    result["Group"]["CreationDate"].should.be.a("datetime.datetime")


@mock_cognitoidp
def test_list_groups():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    result = conn.list_groups(UserPoolId=user_pool_id)

    result["Groups"].should.have.length_of(1)
    result["Groups"][0]["GroupName"].should.equal(group_name)


@mock_cognitoidp
def test_delete_group():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    result = conn.delete_group(GroupName=group_name, UserPoolId=user_pool_id)
    list(result.keys()).should.equal(["ResponseMetadata"])  # No response expected

    with assert_raises(ClientError) as cm:
        conn.get_group(GroupName=group_name, UserPoolId=user_pool_id)
    cm.exception.response['Error']['Code'].should.equal('ResourceNotFoundException')


@mock_cognitoidp
def test_admin_add_user_to_group():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    result = conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)
    list(result.keys()).should.equal(["ResponseMetadata"])  # No response expected


@mock_cognitoidp
def test_admin_add_user_to_group_again_is_noop():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)
    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)


@mock_cognitoidp
def test_list_users_in_group():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)

    result = conn.list_users_in_group(UserPoolId=user_pool_id, GroupName=group_name)

    result["Users"].should.have.length_of(1)
    result["Users"][0]["Username"].should.equal(username)


@mock_cognitoidp
def test_list_users_in_group_ignores_deleted_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)
    username2 = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username2)

    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)
    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username2, GroupName=group_name)
    conn.admin_delete_user(UserPoolId=user_pool_id, Username=username)

    result = conn.list_users_in_group(UserPoolId=user_pool_id, GroupName=group_name)

    result["Users"].should.have.length_of(1)
    result["Users"][0]["Username"].should.equal(username2)


@mock_cognitoidp
def test_admin_list_groups_for_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)

    result = conn.admin_list_groups_for_user(Username=username, UserPoolId=user_pool_id)

    result["Groups"].should.have.length_of(1)
    result["Groups"][0]["GroupName"].should.equal(group_name)


@mock_cognitoidp
def test_admin_list_groups_for_user_ignores_deleted_group():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)
    group_name2 = str(uuid.uuid4())
    conn.create_group(GroupName=group_name2, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)
    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name2)
    conn.delete_group(GroupName=group_name, UserPoolId=user_pool_id)

    result = conn.admin_list_groups_for_user(Username=username, UserPoolId=user_pool_id)

    result["Groups"].should.have.length_of(1)
    result["Groups"][0]["GroupName"].should.equal(group_name2)


@mock_cognitoidp
def test_admin_remove_user_from_group():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)

    result = conn.admin_remove_user_from_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)
    list(result.keys()).should.equal(["ResponseMetadata"])  # No response expected
    conn.list_users_in_group(UserPoolId=user_pool_id, GroupName=group_name) \
        ["Users"].should.have.length_of(0)
    conn.admin_list_groups_for_user(Username=username, UserPoolId=user_pool_id) \
        ["Groups"].should.have.length_of(0)


@mock_cognitoidp
def test_admin_remove_user_from_group_again_is_noop():
    conn = boto3.client("cognito-idp", "us-west-2")

    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    group_name = str(uuid.uuid4())
    conn.create_group(GroupName=group_name, UserPoolId=user_pool_id)

    username = str(uuid.uuid4())
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)
    conn.admin_add_user_to_group(UserPoolId=user_pool_id, Username=username, GroupName=group_name)


@mock_cognitoidp
def test_admin_create_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    result = conn.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=[
            {"Name": "thing", "Value": value}
        ],
    )

    result["User"]["Username"].should.equal(username)
    result["User"]["UserStatus"].should.equal("FORCE_CHANGE_PASSWORD")
    result["User"]["Attributes"].should.have.length_of(1)
    result["User"]["Attributes"][0]["Name"].should.equal("thing")
    result["User"]["Attributes"][0]["Value"].should.equal(value)
    result["User"]["Enabled"].should.equal(True)


@mock_cognitoidp
def test_admin_get_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    value = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=[
            {"Name": "thing", "Value": value}
        ],
    )

    result = conn.admin_get_user(UserPoolId=user_pool_id, Username=username)
    result["Username"].should.equal(username)
    result["UserAttributes"].should.have.length_of(1)
    result["UserAttributes"][0]["Name"].should.equal("thing")
    result["UserAttributes"][0]["Value"].should.equal(value)


@mock_cognitoidp
def test_admin_get_missing_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    caught = False
    try:
        conn.admin_get_user(UserPoolId=user_pool_id, Username=username)
    except conn.exceptions.UserNotFoundException:
        caught = True

    caught.should.be.true


@mock_cognitoidp
def test_list_users():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)
    result = conn.list_users(UserPoolId=user_pool_id)
    result["Users"].should.have.length_of(1)
    result["Users"][0]["Username"].should.equal(username)


@mock_cognitoidp
def test_list_users_returns_limit_items():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 users
    user_count = 10
    for i in range(user_count):
        conn.admin_create_user(UserPoolId=user_pool_id,
                               Username=str(uuid.uuid4()))
    max_results = 5
    result = conn.list_users(UserPoolId=user_pool_id, Limit=max_results)
    result["Users"].should.have.length_of(max_results)
    result.should.have.key("PaginationToken")


@mock_cognitoidp
def test_list_users_returns_pagination_tokens():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 users
    user_count = 10
    for i in range(user_count):
        conn.admin_create_user(UserPoolId=user_pool_id,
                               Username=str(uuid.uuid4()))

    max_results = 5
    result = conn.list_users(UserPoolId=user_pool_id, Limit=max_results)
    result["Users"].should.have.length_of(max_results)
    result.should.have.key("PaginationToken")

    next_token = result["PaginationToken"]
    result_2 = conn.list_users(UserPoolId=user_pool_id,
                               Limit=max_results, PaginationToken=next_token)
    result_2["Users"].should.have.length_of(max_results)
    result_2.shouldnt.have.key("PaginationToken")


@mock_cognitoidp
def test_list_users_when_limit_more_than_total_items():
    conn = boto3.client("cognito-idp", "us-west-2")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Given 10 users
    user_count = 10
    for i in range(user_count):
        conn.admin_create_user(UserPoolId=user_pool_id,
                               Username=str(uuid.uuid4()))

    max_results = user_count + 5
    result = conn.list_users(UserPoolId=user_pool_id, Limit=max_results)
    result["Users"].should.have.length_of(user_count)
    result.shouldnt.have.key("PaginationToken")


@mock_cognitoidp
def test_admin_disable_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)

    result = conn.admin_disable_user(UserPoolId=user_pool_id, Username=username)
    list(result.keys()).should.equal(["ResponseMetadata"])  # No response expected

    conn.admin_get_user(UserPoolId=user_pool_id, Username=username) \
        ["Enabled"].should.equal(False)


@mock_cognitoidp
def test_admin_enable_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)
    conn.admin_disable_user(UserPoolId=user_pool_id, Username=username)

    result = conn.admin_enable_user(UserPoolId=user_pool_id, Username=username)
    list(result.keys()).should.equal(["ResponseMetadata"])  # No response expected

    conn.admin_get_user(UserPoolId=user_pool_id, Username=username) \
        ["Enabled"].should.equal(True)


@mock_cognitoidp
def test_admin_delete_user():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    conn.admin_create_user(UserPoolId=user_pool_id, Username=username)
    conn.admin_delete_user(UserPoolId=user_pool_id, Username=username)

    caught = False
    try:
        conn.admin_get_user(UserPoolId=user_pool_id, Username=username)
    except conn.exceptions.UserNotFoundException:
        caught = True

    caught.should.be.true


def authentication_flow(conn):
    username = str(uuid.uuid4())
    temporary_password = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    user_attribute_name = str(uuid.uuid4())
    user_attribute_value = str(uuid.uuid4())
    client_id = conn.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=str(uuid.uuid4()),
        ReadAttributes=[user_attribute_name]
    )["UserPoolClient"]["ClientId"]

    conn.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        TemporaryPassword=temporary_password,
        UserAttributes=[{
            'Name': user_attribute_name,
            'Value': user_attribute_value
        }]
    )

    result = conn.admin_initiate_auth(
        UserPoolId=user_pool_id,
        ClientId=client_id,
        AuthFlow="ADMIN_NO_SRP_AUTH",
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": temporary_password
        },
    )

    # A newly created user is forced to set a new password
    result["ChallengeName"].should.equal("NEW_PASSWORD_REQUIRED")
    result["Session"].should_not.be.none

    # This sets a new password and logs the user in (creates tokens)
    new_password = str(uuid.uuid4())
    result = conn.respond_to_auth_challenge(
        Session=result["Session"],
        ClientId=client_id,
        ChallengeName="NEW_PASSWORD_REQUIRED",
        ChallengeResponses={
            "USERNAME": username,
            "NEW_PASSWORD": new_password
        }
    )

    result["AuthenticationResult"]["IdToken"].should_not.be.none
    result["AuthenticationResult"]["AccessToken"].should_not.be.none

    return {
        "user_pool_id": user_pool_id,
        "client_id": client_id,
        "id_token": result["AuthenticationResult"]["IdToken"],
        "access_token": result["AuthenticationResult"]["AccessToken"],
        "username": username,
        "password": new_password,
        "additional_fields": {
            user_attribute_name: user_attribute_value
        }
    }


@mock_cognitoidp
def test_authentication_flow():
    conn = boto3.client("cognito-idp", "us-west-2")

    authentication_flow(conn)


@mock_cognitoidp
def test_token_legitimacy():
    conn = boto3.client("cognito-idp", "us-west-2")

    path = "../../moto/cognitoidp/resources/jwks-public.json"
    with open(os.path.join(os.path.dirname(__file__), path)) as f:
        json_web_key = json.loads(f.read())["keys"][0]

    outputs = authentication_flow(conn)
    id_token = outputs["id_token"]
    access_token = outputs["access_token"]
    client_id = outputs["client_id"]
    issuer = "https://cognito-idp.us-west-2.amazonaws.com/{}".format(outputs["user_pool_id"])
    id_claims = json.loads(jws.verify(id_token, json_web_key, "RS256"))
    id_claims["iss"].should.equal(issuer)
    id_claims["aud"].should.equal(client_id)
    access_claims = json.loads(jws.verify(access_token, json_web_key, "RS256"))
    access_claims["iss"].should.equal(issuer)
    access_claims["aud"].should.equal(client_id)
    for k, v in outputs["additional_fields"].items():
        access_claims[k].should.equal(v)


@mock_cognitoidp
def test_change_password():
    conn = boto3.client("cognito-idp", "us-west-2")

    outputs = authentication_flow(conn)

    # Take this opportunity to test change_password, which requires an access token.
    newer_password = str(uuid.uuid4())
    conn.change_password(
        AccessToken=outputs["access_token"],
        PreviousPassword=outputs["password"],
        ProposedPassword=newer_password,
    )

    # Log in again, which should succeed without a challenge because the user is no
    # longer in the force-new-password state.
    result = conn.admin_initiate_auth(
        UserPoolId=outputs["user_pool_id"],
        ClientId=outputs["client_id"],
        AuthFlow="ADMIN_NO_SRP_AUTH",
        AuthParameters={
            "USERNAME": outputs["username"],
            "PASSWORD": newer_password,
        },
    )

    result["AuthenticationResult"].should_not.be.none


@mock_cognitoidp
def test_forgot_password():
    conn = boto3.client("cognito-idp", "us-west-2")

    result = conn.forgot_password(ClientId=str(uuid.uuid4()), Username=str(uuid.uuid4()))
    result["CodeDeliveryDetails"].should_not.be.none


@mock_cognitoidp
def test_confirm_forgot_password():
    conn = boto3.client("cognito-idp", "us-west-2")

    username = str(uuid.uuid4())
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
    client_id = conn.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=str(uuid.uuid4()),
    )["UserPoolClient"]["ClientId"]

    conn.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        TemporaryPassword=str(uuid.uuid4()),
    )

    conn.confirm_forgot_password(
        ClientId=client_id,
        Username=username,
        ConfirmationCode=str(uuid.uuid4()),
        Password=str(uuid.uuid4()),
    )
