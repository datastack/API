import boto3
import logging

from os import getenv

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)',
    datefmt='%d/%m/%Y %I:%M:%S %p',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')

sess = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                     region_name='us-east-1')

elb = sess.client('elb')
ec2 = sess.client('ec2')


def list_elb_instances(name):
    """
    :param name: string to query ELB by name
    :return: list containing elb instances-id attached.
        on error return None
    """
    try:
        instances_docs = []
        if not isinstance(name, str):
            raise ValueError('Invalid argument type. Must be a > string')
        elb_response = elb.describe_load_balancers(
            LoadBalancerNames=[name]
        )
        for info in elb_response.get('LoadBalancerDescriptions'):
            instances = info.get('Instances')
            for ins in instances:
                ins_doc = get_ec2_info(ins.get('InstanceId'))
                instances_docs.append(ins_doc)
        return instances_docs
    except Exception as e:
        logger.exception(e)
        return None


def get_ec2_info(instid):
    """
    Method to get ec2 instance informations
    :param instid: string format of AWS EC2 InstanceId
    Ex: example: i-5203422c
    :return: dict containing MachineInfo Object Especification
        on error return None
    """
    machine_info = {}
    try:
        if not isinstance(instid, str):
            raise ValueError('Invalid argument type. Must be a > string')
        ec2_response = ec2.describe_instances(
            InstanceIds=[instid]
        )
    except Exception as e:
        logger.exception(e)
        return None

    if ec2_response:
        try:
            ec2_info = ec2_response.get('Reservations')[0].get('Instances')[0]
            machine_info['instanceId'] = ec2_info.get('InstanceId')
            machine_info['instanceType'] = ec2_info.get('InstanceType')
            machine_info['launchDate'] = ec2_info.get('LaunchTime').strftime("%Y-%m-%dT%H:%M:%fZ")
            return machine_info
        except Exception as e:
            logger.exception(e)
            return None


def add_instance_on_elb(elbnm, instid):
    """
    Function used to add new instances into ELB
    :param elbnm: string -> ELB name
    :param instid: string -> the instanceId to add on ELB
    :return: dict with key 'status'
        201 - Instance added OK
        409 - Instance already attached on ELB
        or None if error
    """
    try:
        elb_instances = list_elb_instances(elbnm)
        for inst in elb_instances:
            if inst.get('instanceId') == instid:
                return {'status': 409}
        response = elb.register_instances_with_load_balancer(
            LoadBalancerName=elbnm,
            Instances=[
                {
                    'InstanceId': instid
                },
            ]
        )
        if response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
            return {'status': 201, 'info': get_ec2_info(instid)}
    except Exception as e:
        logger.error(e)
        return None


def rem_instance_from_elb(elbnm, instid):
    """
    Function used to remove instances from ELB
    :param elbnm: string -> ELB name
    :param instid: string -> the instanceId to remove on ELB
    :return: dict with key 'status'
        201 - Instance removed OK
        409 - Instance is not attached on ELB
        or None if error
    """
    try:
        exists = False
        elb_instances = list_elb_instances(elbnm)
        for inst in elb_instances:
            if inst.get('instanceId') == instid:
                exists = True
        if not exists:
            return {'status': 409}
        response = elb.deregister_instances_from_load_balancer(
            LoadBalancerName=elbnm,
            Instances=[
                {
                    'InstanceId': instid
                },
            ]
        )
        if response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
            return {'status': 201, 'info': get_ec2_info(instid)}
    except Exception as e:
        logger.exception(e)
        return None
