import base64
import boto3
import ConfigParser
import json
import sys


config = ConfigParser.ConfigParser()
config.read('./instance.conf')


if len(sys.argv) != 2:
    print("USAGE: %s {TAG_NAME}")
    sys.exit(1)
TAG_NAME = sys.argv[1]


def _create_spot_instances():
    print("creating spot request")
    with open('./user_data', 'r') as f:
        user_data = f.read()
    ec2_client = boto3.client('ec2')
    ec2_response = ec2_client.request_spot_instances(
        SpotPrice = config.get('spot_instance', 'spot_price'),
        InstanceCount = 1,
        Type = 'persistent',
        LaunchSpecification={
                'ImageId': config.get('spot_instance', 'ami_id'),
                'KeyName': config.get('spot_instance', 'key_name'),
                'SecurityGroups': json.loads(config.get('spot_instance', 'security_groups')),
                'UserData': base64.b64encode(user_data),
                'InstanceType': config.get('spot_instance', 'instance_type'),
                'Placement': {
                    'AvailabilityZone': config.get('spot_instance', 'zone'),
                    'GroupName': ''
                },
            }
        )
    spot_requests_id_list = [request['SpotInstanceRequestId'] for request in ec2_response['SpotInstanceRequests']]
    return spot_requests_id_list


def _get_instance_info(spot_request_id_list = []):
    ec2_client = boto3.client('ec2')
    filter_rule_list = [{'Name': 'spot-instance-request-id', 'Values': spot_request_id_list}]
    instance_list = []
    print("waiting for instance")
    while not len(instance_list) == len(spot_request_id_list):
        ec2_response = ec2_client.describe_instances(Filters=filter_rule_list)
        response_instance_list = []
        for i in ec2_response['Reservations']:
            response_instance_list += i['Instances']
        instance_list = [
            {
                'instance_id': i['InstanceId'],
                'private_ip': i['PrivateIpAddress'],
                'public_ip': i['PublicIpAddress'],
            }
            for i in response_instance_list
        ]
    return instance_list


def _tag_resource(resource_id_list = []):
    print("tagging resource: %s" % (','.join(resource_id_list)))
    ec2 = boto3.client('ec2')
    tags_list = [{'Key': 'Name', 'Value': TAG_NAME}]
    ec2.create_tags(
        Resources = resource_id_list,
        Tags = tags_list
    )


if __name__ == '__main__':
    spot_request_id_list = _create_spot_instances()
    print("spot request created: %s" % (','.join(spot_request_id_list)))
    _tag_resource(spot_request_id_list)
    instance_list = _get_instance_info(spot_request_id_list)
    instance_ip_list = [ instance['public_ip'] for instance in instance_list ]
    print("instance ip: %s" % (','.join(instance_ip_list)))
    instance_id_list = [ instance['instance_id'] for instance in instance_list ]
    _tag_resource(instance_id_list)
