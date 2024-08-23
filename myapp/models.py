from django.db import models
from django.core.validators import FileExtensionValidator
class Apk(models.Model):  
    apk_name = models.CharField(max_length=100)  
    app_name = models.CharField(max_length=100,null=True, blank=True)  
    package = models.CharField(max_length=100,null=True, blank=True)  
    androidversion_name = models.CharField(max_length=100,null=True, blank=True)  
    effective_target_sdk_version = models.CharField(max_length=100, null=True, blank=True)  
    md5_code = models.CharField(max_length=500, unique=True)
    is_black = models.BooleanField(default=False)
    is_signed = models.BooleanField(default=True)
    category = models.CharField(max_length=20, default='正常')
    code_result = models.CharField(max_length=20, default='正常')
    confidence_level = models.CharField(max_length=50, default='1')
    state = models.CharField(max_length=20, default='获取apk')
    report = models.FileField(upload_to='documents/',null=True) 
    apk_file = models.FileField(upload_to='apk_files/',null=True) 
    icon = models.ImageField(upload_to='icons/', validators=[  
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])  
    ], default='default.jpeg')
    apk_size = models.CharField(max_length=20, default='0B')
    time = models.DateTimeField(auto_now_add=True)
    conclusion = models.CharField(max_length=300, default='')
    
    
class Website(models.Model):  
    url = models.CharField(max_length=200)  
    ip = models.CharField(max_length=50, null=True, blank=True)  
    domain_name = models.CharField(max_length=100)  
    city = models.CharField(max_length=100, null=True, blank=True)  
    region = models.CharField(max_length=100, null=True, blank=True) 
    country = models.CharField(max_length=100, null=True, blank=True) 
    is_black = models.BooleanField(default=False)
    apk = models.ForeignKey(Apk, on_delete=models.CASCADE) 
    
class Permission(models.Model):  
    name = models.CharField(max_length=100)  
    discription = models.CharField(max_length=200, null=True, blank=True)
    chinese_name = models.CharField(max_length=50, null=True, blank=True) 
    is_danger = models.BooleanField(default=False)
    level = models.IntegerField(default=0)
    apk = models.ForeignKey(Apk, on_delete=models.CASCADE) 
    
    
class Cirtification(models.Model):  
    serial_number = models.CharField(max_length=50)  
    sha1_code = models.CharField(max_length=500,null=True,blank=True) 
    sha256_code = models.CharField(max_length=500,null=True,blank=True) 
    start_time = models.CharField(max_length=50,null=True,blank=True) 
    end_time = models.CharField(max_length=50,null=True,blank=True) 
    version = models.CharField(max_length=10,null=True,blank=True)
    signature_algorithm =  models.CharField(max_length=50,null=True,blank=True) 
    public_key_algorithm =  models.CharField(max_length=50,null=True,blank=True) 
    apk = models.ForeignKey(Apk, on_delete=models.CASCADE) 
    
class BlackPicture(models.Model): 
    category = models.CharField(max_length=20, default='黑色产业')
    file_path = models.CharField(max_length=300) 
    picture = models.ImageField(upload_to='black_pictures/', validators=[  
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])  
    ])
    apk = models.ForeignKey(Apk, on_delete=models.CASCADE) 
