import boto3
import os

class AddInstanceSubdomain:
    def __init__(self):        
        self.access_key = os.environ.get('PUBLIC_KEY')
        self.secret_key = os.environ.get('PRIVATE_KEY')
        self.r53 = boto3.client('route53', region_name='us-east-1', aws_access_key_id=self.access_key,aws_secret_access_key=self.secret_key)
        self.ec2 = boto3.client('ec2', region_name='us-east-1', aws_access_key_id=self.access_key,aws_secret_access_key=self.secret_key)
        self.hosted_zone = self.get_hosted_zone()
        self.vpc_id = 'vpc-5c158c21'

    def fetchall_instances(self):
        return self.ec2.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [self.vpc_id, ]}, ])

    def get_hosted_zone(self, domain='si3mshady.com'):
        return [i['Id'] for i in self.r53.list_hosted_zones()['HostedZones'] \
                    if domain in i['Name']][0].split('/')[-1]

    def add_complete_tag(self,instance_id):
        #tag instances once added to domain
        response = self.ec2.create_tags(
            DryRun=False,
            Resources=[
                instance_id
            ],
            Tags=[
                {
                    'Key': 'added to domain',
                    'Value': f'{instance_id}.si3mshady.com'
                },
            ]
        )


    def check_instance_added_to_domain(self):
        try:
            for i in self.fetchall_instances()['Reservations']:
                if len(i['Instances'][0]['Tags']) >=1:
                    if len(i['Instances'][0]['Tags']) == 1:
                        if  'add_to_domain' not in i['Instances'][0]['Tags'][0]['Key']:
                            self.add_subdomain(i['Instances'][0]['InstanceId'],i['Instances'][0]['PublicIpAddress'])
                            return  {"statusCode": 200, "headers": \
                                {"Access-Control-Allow-Origin": "*"},"body": "added new instance to domain"} 

                    else:
                        if len(i['Instances'][0]['Tags']) == 2:
                            print(i['Instances'][0]['Tags'][1]['Value'])
                            print(i['Instances'][0]['Tags'][0]['Value'])
                            if 'si3mshady.com' in i['Instances'][0]['Tags'][0]['Value'] or 'si3mshady.com' \
                                 in i['Instances'][0]['Tags'][1]['Value']:
                                print('Already_added',i['Instances'][0]['InstanceId'],i['Instances'][0]['PublicIpAddress'])
                                return  {"statusCode": 200, "headers":\
                                     {"Access-Control-Allow-Origin": "*"},"body": "instance already added to domain"} 


        except KeyError:
            pass

    def add_subdomain(self,instance_id,public_ip):
        self.add_complete_tag(instance_id)
        self.r53.change_resource_record_sets(
            HostedZoneId=self.hosted_zone,
            ChangeBatch={
                'Comment': f'Adding subdomain {instance_id}.si3mshady.com',
                'Changes': [
                    {
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': f'{instance_id}.si3mshady.com',
                            'Type': 'A',
                    'TTL': 120,

                            'ResourceRecords': [
                        {
                            'Value': public_ip
                        }],



                        }
                    },
                ]
            }
        )
        return 
       

def lambda_handler(event,context):
    checker = AddInstanceSubdomain()
    return checker.check_instance_added_to_domain()
  

#AWS Lambda DNS Route53 practice exercise
#Use cloudwatch trigger to check for new instances to add to public domain
#Instances carrying appropriate tag will have an create 'A' record and subdomain created allowing ssh access using public DNS name
#Elliott Arnold
#3-14-2020


#updated 6-21-21