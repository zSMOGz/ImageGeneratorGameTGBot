# Для входа в huggingface.co ввести учётные данные через команду:
# huggingface-cli login
import torch

from diffusers import (StableCascadeCombinedPipeline as scPipeline,
                       AutoPipelineForText2Image as autoPipeline,
                       DiffusionPipeline,
                       DDIMScheduler)
from huggingface_hub import login
from config import HAGGINGFACE_TOKEN

login(token=HAGGINGFACE_TOKEN)

IMAGE_PATH = "images/"
IMAGE_NAME_SD = "image_sd.png"
IMAGE_NAME_KD = "image_kd.png"
IMAGE_NAME_SK = "image_sk.png"

NEURO_PATH = "./neuro_models/"
STABLE_DIFFUSION_PATH = "stable-diffusion-xl-base-1.0"
KANDINSKY_PATH = "kandinsky-2-1"
STABLE_CASCADE_PATH = "stable-cascade"

CUDA = "cuda"
NEGATIVE_PROMPT = "low quality, bad quality"
NUM_INFERENCE_STEPS = 50
PRIOR_NUM_INFERENCE_STEPS = 30
PRIOR_GUIDANCE_SCALE = 3.0
IMAGE_HEIGHT = 1024
IMAGE_WIDTH = 1024


class ImageGenerator:
    """
    Основной класс для генерации изображений.

    Attributes:
        model_id: Имя модели.
        pipe: Последовательность элементов модели.
        image: Изображение.
        image_name: Имя изображения.
    """

    def __init__(self,
                 model_id,
                 pipe,
                 image_name=IMAGE_NAME_SD):
        self.model_id = model_id
        self.pipe = pipe
        self.image = None
        self.image_name = image_name

    def generate_image(self,
                       prompt: str):
        """
        Генерация изображения по текстовому описанию.

        Parameters:
            prompt(srt): Текстовое описание, по которому генерируется
            изображение.

        Returns:
            str: Путь к изображению на сервере.
        """
        pass


class StableDiffusion(ImageGenerator):
    """
    Генератор изображений с использованием Stable Diffusion.
    """

    def __init__(self):
        self.model_id = NEURO_PATH + STABLE_DIFFUSION_PATH
        self.ddim = DDIMScheduler.from_pretrained(self.model_id,
                                                  subfolder="scheduler")
        self.pipe = DiffusionPipeline.from_pretrained(self.model_id,
                                                      ddim=self.ddim,
                                                      torch_dtype=torch.float16
                                                      )
        self.pipe = self.pipe.to(CUDA)
        super().__init__(self.model_id,
                         self.pipe,
                         image_name=IMAGE_NAME_SD)

    def generate_image(self,
                       prompt):
        try:
            image = self.pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=NUM_INFERENCE_STEPS,
                prior_num_inference_steps=PRIOR_NUM_INFERENCE_STEPS,
                prior_guidance_scale=PRIOR_GUIDANCE_SCALE,
                height=IMAGE_HEIGHT,
                width=IMAGE_WIDTH,
                # guidance_scale=7.0,
            ).images[0]

            image.save(IMAGE_PATH + self.image_name)

            return IMAGE_PATH + self.image_name
        except Exception as e:
            print(e)
            return None


class Kandinsky(ImageGenerator):
    """
    Генератор изображений с использованием нейросети Kandinsky.
    """

    def __init__(self):
        self.model_id = NEURO_PATH + KANDINSKY_PATH
        self.pipe = autoPipeline.from_pretrained(self.model_id,
                                                 torch_dtype=torch.float16)
        self.pipe = self.pipe.to(CUDA)
        super().__init__(self.model_id,
                         self.pipe,
                         image_name=IMAGE_NAME_KD)

    def generate_image(self,
                       prompt):
        try:
            image = self.pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=NUM_INFERENCE_STEPS,
                prior_num_inference_steps=PRIOR_NUM_INFERENCE_STEPS,
                prior_guidance_scale=PRIOR_GUIDANCE_SCALE,
                height=IMAGE_HEIGHT,
                width=IMAGE_WIDTH,
            ).images[0]

            image.save(IMAGE_PATH + self.image_name)

            return IMAGE_PATH + self.image_name
        except Exception as e:
            print(e)
            return None


class StableCascade(ImageGenerator):
    """
    Генератор изображений с использованием нейросети Stable Cascade.
    """

    def __init__(self):
        self.model_id = NEURO_PATH + STABLE_CASCADE_PATH
        self.pipe = scPipeline.from_pretrained(self.model_id,
                                               variant="bf16",
                                               torch_dtype=torch.bfloat16)
        self.pipe = self.pipe.to(CUDA)
        super().__init__(self.model_id,
                         self.pipe,
                         image_name=IMAGE_NAME_SK)

    def generate_image(self,
                       prompt):
        try:
            image = self.pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=NUM_INFERENCE_STEPS,
                prior_num_inference_steps=PRIOR_NUM_INFERENCE_STEPS,
                prior_guidance_scale=PRIOR_GUIDANCE_SCALE,
                height=IMAGE_HEIGHT,
                width=IMAGE_WIDTH,
            ).images[0]

            image.save(IMAGE_PATH + self.image_name)

            return IMAGE_PATH + self.image_name
        except Exception as e:
            print(e)
            return None
