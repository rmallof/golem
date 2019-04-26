import math
import random
from typing import Tuple, List, Optional
import numpy

WORK_DIR = "/golem/work"
OUTPUT_DIR = "/golem/output"
CROP_RELATIVE_SIZE = 0.1
MIN_CROP_SIZE = 8


class FloatingPointBox:
    """
    This class stores values of image region expressed with floating point
    numbers as a percentage of image corresponding resolution.
    It mimic blender coordinate system, when trying to render partial image.
    """
    def __init__(
            self,
            left: float,
            top: float,
            right: float,
            bottom: float
    ) -> None:
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    def __contains__(self, item: 'FloatingPointBox') -> bool:
        """
       l, t _______
           |    <--|-- self
           |  ____ |
           | |  <-||-- item
           | |____||
           |_______|r, b
        """
        return item.left >= self.left and item.right <= self.right and \
               item.top >= self.top and item.bottom <= self.bottom


class PixelRegion:
    """
    Similar to Region class, but floats have been calculated to int, by
    multiplying with resolution and vertical coordinate have been reversed, so
    that it's mimicking coordinate system of libraries like PIL and OpenCV.
    """
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom


# todo review: this shouldn't be a separate class, move and rename its
#  attributes (with indication that they describe subtask) and methods to Crop,
#  where they logically belong
class SubImage:
    def __init__(self, region: FloatingPointBox, resolution: List[int]) -> None:
        # todo review: rename "region" after renaming "Region" class
        self.region = region
        self.resolution = resolution


class NewCrop:
    STEP_SIZE = 0.01

    def __init__(
            self,
            id: int,
            resolution: List[int],
            subtask_box: FloatingPointBox,
            crop_box: Optional[FloatingPointBox] = None
    ):
        self.id = id
        self.resolution = resolution
        self._subtask_box = subtask_box
        self.box = crop_box or self._generate_random_crop_box()
        self._validate_crop_is_within_subtask()

    @property
    def x_pixels(self):
        return self._get_x_coordinates_as_pixels()

    @property
    def y_pixels(self):
        return self._get_y_coordinates_as_pixels()

    def _generate_random_crop_box(self) -> FloatingPointBox:
        crop_width, crop_height = self._get_relative_crop_size()

        print(f'-> subtask_box.left={self._subtask_box.left}')
        print(f'-> subtask_box.right={self._subtask_box.right}')
        print(f'-> subtask_box.top={self._subtask_box.top}')
        print(f'-> subtask_box.bottom={self._subtask_box.bottom}')

        x_beginning, x_end = self._get_coordinate_limits(
            lower_border=self._subtask_box.left,
            upper_border=self._subtask_box.right,
            span=crop_width
        )
        print(f"x_beginning={x_beginning}, x_end={x_end}")

        # left, top is (0,0) in image coordinates
        y_beginning, y_end = self._get_coordinate_limits(
            lower_border=self._subtask_box.top,
            upper_border=self._subtask_box.bottom,
            span=crop_height
        )
        print(f"y_beginning={y_beginning}, y_end={y_end}")

        return FloatingPointBox(
            left=x_beginning,
            right=x_end,
            top=y_beginning,
            bottom=y_end
        )

    @staticmethod
    def _get_coordinate_limits(lower_border, upper_border, span):
        coordinate_beginning_limit = round((upper_border - span) * 100)
        beginning = random.randint(round(lower_border * 100),
                                   coordinate_beginning_limit) / 100
        end = round(beginning + span, 2)
        return beginning, end

    def _get_relative_crop_size(self) -> Tuple[float, float]:
        relative_crop_width = CROP_RELATIVE_SIZE
        relative_crop_height = CROP_RELATIVE_SIZE
        while relative_crop_width * self.resolution[0] < MIN_CROP_SIZE:
            relative_crop_width += self.STEP_SIZE
        while relative_crop_height * self.resolution[1] < MIN_CROP_SIZE:
            relative_crop_height += self.STEP_SIZE
        print(
            f"relative_crop_width: {relative_crop_width}, "
            f"relative_crop_height: {relative_crop_height}"
        )
        return relative_crop_width, relative_crop_height

    def _validate_crop_is_within_subtask(self):
        if self.box not in self._subtask_box:
            raise ValueError("Crop box is not within subtask box!")

    def _get_x_coordinates_as_pixels(self) -> Tuple[int, int]:
        x_pixel_min = math.floor(
            numpy.float32(self.resolution[0]) * numpy.float32(
                self.box.left
            )
        ) - math.floor(
            numpy.float32(self._subtask_box.left) * numpy.float32(
                self.resolution[0])
        )

        x_pixel_max = math.floor(
            numpy.float32(self.resolution[0]) * numpy.float32(
                self.box.right)
        )
        print(f"x_pixel_min={x_pixel_min}, x_pixel_max={x_pixel_max}")
        return x_pixel_min, x_pixel_max

    def _get_y_coordinates_as_pixels(self) -> Tuple[int, int]:
        y_pixel_min = math.floor(
            numpy.float32(self._subtask_box.bottom) * numpy.float32(
                self.resolution[1])
        ) - math.floor(
            numpy.float32(self.resolution[1]) * numpy.float32(
                self.box.bottom)
        )
        y_pixel_max = math.floor(
            numpy.float32(self._subtask_box.bottom) * numpy.float32(
                self.resolution[1])
        ) - math.floor(
            numpy.float32(self.resolution[1]) * numpy.float32(
                self.box.top)
        )
        print(f"y_pixel_min={y_pixel_min}, y_pixel_max={y_pixel_max}")
        return y_pixel_min, y_pixel_max

    def _calculate_crop_region_to_pixel_region(self):
        # todo review: write helper function for these expressions
        x_pixel_min = math.floor(
            numpy.float32(self.resolution[0]) * numpy.float32(
                self.box.left)
        )
        # todo review: don't reuse x_pixel_min variable, find name properly
        #  describing its first (or second?) occurrence's sens
        x_pixel_min = x_pixel_min - math.floor(
            numpy.float32(self._subtask_box.left) * numpy.float32(
                self.resolution[0])
        )
        x_pixel_max = math.floor(
            numpy.float32(self.resolution[0]) * numpy.float32(
                self.box.right)
        )
        print(f"x_pixel_min={x_pixel_min}, x_pixel_max={x_pixel_max}")
        y_pixel_max = math.floor(
            numpy.float32(self._subtask_box.bottom) * numpy.float32(
                self.resolution[1])
        ) - math.floor(
            numpy.float32(self.resolution[1]) * numpy.float32(
                self.box.bottom)
        )
        y_pixel_min = math.floor(
            numpy.float32(self._subtask_box.bottom) * numpy.float32(
                self.resolution[1])
        ) - math.floor(
            numpy.float32(self.resolution[1]) * numpy.float32(
                self.box.top)
        )
        print(f"y_pixel_max={y_pixel_max}, y_pixel_min={y_pixel_min}")
        return PixelRegion(
            left=x_pixel_min,
            right=x_pixel_max,
            top=y_pixel_max,
            bottom=y_pixel_min
        )


class Crop:
    def __init__(
            self,
            id_: int,
            # todo review: rename, it's unclear what this argument and
            #  corresponding variable store
            subimage: SubImage,
    ) -> None:
        self.id = id_
        self.subimage = subimage
        # todo review: rename, it's unclear what this argument and
        #  corresponding variable store
        self.crop_region = self._get_random_float_region(subimage)
        # todo review: rename (pixel_region of what?)
        self.pixel_region = self._calculate_crop_region_to_pixel_region(
            subimage
        )

    @staticmethod
    def _get_random_float_region(subimage):
        relative_crop_size_x = CROP_RELATIVE_SIZE
        relative_crop_size_y = CROP_RELATIVE_SIZE
        # check resolution, make sure that crop is greather then 8px.
        # todo review: why 0.01? Explain, is it arbitrary or this number comes from
        #  some reasoning?
        while relative_crop_size_x * subimage.resolution[0] < MIN_CROP_SIZE:
            relative_crop_size_x += 0.01
        while relative_crop_size_y * subimage.resolution[1] < MIN_CROP_SIZE:
            relative_crop_size_y += 0.01
        print(
            f"relative_crop_size_x: {relative_crop_size_x}, "
            f"relative_crop_size_y: {relative_crop_size_y}"
        )

        # todo review: rename variables below, it's unclear what they store (scene
        #  is stored in .blend file and crop isn't created here yet - not making
        #  much sens)
        crop_scene_x_max = subimage.region.right
        crop_scene_x_min = subimage.region.left
        crop_scene_y_max = subimage.region.bottom
        crop_scene_y_min = subimage.region.top

        print(f'-> crop_scene_x_min={crop_scene_x_min}')
        print(f'-> crop_scene_x_max={crop_scene_x_max}')
        print(f'-> crop_scene_y_min={crop_scene_y_min}')
        print(f'-> crop_scene_y_max={crop_scene_y_max}')


        # todo review: rename variables below to something more descriptive.
        #  Analogically for the "pixel" equivalents (x_pixel_min, ...)
        x_difference = round((crop_scene_x_max - relative_crop_size_x) * 100)
        x_min = random.randint(round(crop_scene_x_min * 100),
                               x_difference) / 100
        x_max = round(x_min + relative_crop_size_x, 2)
        print(f"x_difference={x_difference}, x_min={x_min}, x_max={x_max}")
        # todo review: looks a lot like a code duplication, create helper function
        y_difference = round((crop_scene_y_max - relative_crop_size_y) * 100)
        y_min = random.randint(round(crop_scene_y_min * 100),
                               y_difference) / 100
        y_max = round(y_min + relative_crop_size_y, 2)
        print(f"y_difference={y_difference}, y_min={y_min}, y_max={y_max}")
        return FloatingPointBox(
            left=x_min,
            right=x_max,
            top=y_min,
            bottom=y_max
        )

    def _calculate_crop_region_to_pixel_region(self, subimage):
        # todo review: write helper function for these expressions
        x_pixel_min = math.floor(
            numpy.float32(subimage.resolution[0]) * numpy.float32(
                self.crop_region.left)
        )
        # todo review: don't reuse x_pixel_min variable, find name properly
        #  describing its first (or second?) occurrence's sens
        x_pixel_min = x_pixel_min - math.floor(
            numpy.float32(subimage.region.left) * numpy.float32(
                subimage.resolution[0])
        )
        x_pixel_max = math.floor(
            numpy.float32(subimage.resolution[0]) * numpy.float32(
                self.crop_region.right)
        )
        print(f"x_pixel_min={x_pixel_min}, x_pixel_max={x_pixel_max}")
        y_pixel_max = math.floor(
            numpy.float32(subimage.region.bottom) * numpy.float32(
                subimage.resolution[1])
        ) - math.floor(
            numpy.float32(subimage.resolution[1]) * numpy.float32(
                self.crop_region.bottom)
        )
        y_pixel_min = math.floor(
            numpy.float32(subimage.region.bottom) * numpy.float32(
                subimage.resolution[1])
        ) - math.floor(
            numpy.float32(subimage.resolution[1]) * numpy.float32(
                self.crop_region.top)
        )
        print(f"y_pixel_max={y_pixel_max}, y_pixel_min={y_pixel_min}")
        return PixelRegion(
            left=x_pixel_min,
            right=x_pixel_max,
            top=y_pixel_max,
            bottom=y_pixel_min
        )
