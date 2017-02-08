# Create Spot Instance

Quick way to request spot instance on AWS.

Usage:

1.  Set instance parameters in `instance.conf`
2.  Set user data in `user_data`
3.  Request for spot instance with following command:

``` bash
python createSpotInstance.py {instance_tag_name}
```

Instance_tag_name will be set in both `request tag:Name` and `instance tag:Name`.

