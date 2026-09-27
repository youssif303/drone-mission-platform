import numpy as np
import math

class PinholeCamera:
    def __init__(self, fx: float, fy: float, cx: float, cy: float, image_width: int, image_height: int):
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.image_width = image_width
        self.image_height = image_height

    def pixel_to_ray(self, u: float, v: float) -> np.ndarray:
        '''
        Convert pixel coordinates to normalized camera ray [x, y, z].
        '''
        x = (u - self.cx) / self.fx
        y = (v - self.cy) / self.fy
        z = 1.0
        ray = np.array([x, y, z])
        return ray / np.linalg.norm(ray)

    @classmethod
    def from_fov(cls, fov_deg: float, image_width: int, image_height: int) -> 'PinholeCamera':
        '''
        Compute fx, fy from field of view (horizontal).
        '''
        fov_rad = math.radians(fov_deg)
        fx = (image_width / 2.0) / math.tan(fov_rad / 2.0)
        fy = fx # Assuming square pixels
        cx = image_width / 2.0
        cy = image_height / 2.0
        return cls(fx, fy, cx, cy, image_width, image_height)
