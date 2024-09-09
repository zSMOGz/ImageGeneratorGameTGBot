#pip install --upgrade huggingface_hub
#huggingface-cli login
#pip install diffusers
#pip install transformers==4.22.1
#pip install invisible_watermark accelerate safetensors
#pip install 'huggingface_hub[cli,torch]'
#pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
#pip install --upgrade transformers accelerate
#pip install SentencePiece
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import torch

from diffusers import (StableCascadeCombinedPipeline,
                       AutoPipelineForText2Image,
                       DiffusionPipeline,
                       DDIMScheduler)
from huggingface_hub import login
from PIL import Image
from config import HAGGINGFAVE_TOKEN

login(token=HAGGINGFAVE_TOKEN)

IMAGE_PATH = "images/"
IMAGE_NAME_SD = "image_sd.png"
IMAGE_NAME_KD = "image_kd.png"
IMAGE_NAME_SK = "image_sk.png"


class ImageGenerator:
    def __init__(self,
                 model_id,
                 pipe,
                 image_name=IMAGE_NAME_SD):
        self.model_id = model_id
        self.pipe = pipe
        self.image = None
        self.image_name = image_name

    def generate_image(self,
                       prompt):
        pass


class StableDiffusion(ImageGenerator):
    def __init__(self):
        self.model_id = "./neiro_models/stable-diffusion-xl-base-1.0"
        self.ddim = DDIMScheduler.from_pretrained(self.model_id,
                                                  subfolder="scheduler")
        self.pipe = DiffusionPipeline.from_pretrained(self.model_id,
                                                      ddim=self.ddim,
                                                      torch_dtype=torch.float16)
        self.pipe = self.pipe.to("cuda")
        super().__init__(self.model_id,
                         self.pipe,
                         image_name=IMAGE_NAME_SD)

    def generate_image(self,
                       prompt):
        try:
            image = self.pipe(
                prompt=prompt,
                negative_prompt="low quality, bad quality",
                num_inference_steps=50,
                prior_num_inference_steps=30,
                prior_guidance_scale=3.0,
                height=1024,
                width=1024,
                guidance_scale=7.0,
            ).images[0]

            image.save(IMAGE_PATH + self.image_name)

            return IMAGE_PATH + self.image_name
        except Exception as e:
            print(e)
            return None


class Kandinsky(ImageGenerator):
    def __init__(self):
        self.model_id = "./neiro_models/kandinsky-2-1"
        self.pipe = AutoPipelineForText2Image.from_pretrained(self.model_id,
                                                              torch_dtype=torch.float16)
        self.pipe = self.pipe.to("cuda")
        super().__init__(self.model_id,
                         self.pipe,
                         image_name=IMAGE_NAME_KD)

    def generate_image(self,
                       prompt):
        try:
            image = self.pipe(
                prompt=prompt,
                negative_prompt="low quality, bad quality",
                num_inference_steps=50,
                prior_num_inference_steps=30,
                prior_guidance_scale=3.0,
                height=1024,
                width=1024,
            ).images[0]

            image.save(IMAGE_PATH + self.image_name)

            return IMAGE_PATH + self.image_name
        except Exception as e:
            print(e)
            return None


class StableCascade(ImageGenerator):
    def __init__(self):
        self.model_id = "./neiro_models/stable-cascade"
        self.pipe = StableCascadeCombinedPipeline.from_pretrained(self.model_id,
                                                                  variant="bf16",
                                                                  torch_dtype=torch.bfloat16)
        self.pipe = self.pipe.to("cuda")
        super().__init__(self.model_id,
                         self.pipe,
                         image_name=IMAGE_NAME_SK)

    def generate_image(self,
                       prompt):
        try:
            image = self.pipe(
                prompt=prompt,
                negative_prompt="low quality, bad quality",
                num_inference_steps=50,
                prior_num_inference_steps=30,
                prior_guidance_scale=3.0,
                height=1024,
                width=1024,
            ).images[0]

            image.save(IMAGE_PATH + self.image_name)

            return IMAGE_PATH + self.image_name
        except Exception as e:
            print(e)
            return None
