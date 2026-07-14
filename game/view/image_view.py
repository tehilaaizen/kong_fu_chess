from __future__ import annotations

import pathlib

import cv2
import numpy as np


class Img:
    """Thin wrapper around the course-supplied opencv-python image
    library: load, resize, blend and annotate images without any of the
    rest of the codebase needing to know it's opencv underneath."""

    def __init__(self) -> None:
        """Create an empty Img holding no image data yet."""
        self.img: np.ndarray | None = None

    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> "Img":
        """
        Load `path` into self.img and **optionally resize**.

        Parameters
        ----------
        path : str | Path
            Image file to load.
        size : (width, height) | None
            Target size in pixels.  If None, keep original.
        keep_aspect : bool
            • False  → resize exactly to `size`
            • True   → shrink so the *longer* side fits `size` while
                       preserving aspect ratio (no cropping).
        interpolation : OpenCV flag
            E.g.  `cv2.INTER_AREA` for shrink, `cv2.INTER_LINEAR` for enlarge.

        Returns
        -------
        Img
            `self`, so you can chain:  `sprite = Img().read("foo.png", (64,64))`
        """
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            raise FileNotFoundError(f"Cannot load image: {path}")

        if size is not None:
            target_w, target_h = size
            h, w = self.img.shape[:2]

            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h

            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)

        return self

    def to_rgba(self) -> "Img":
        """Ensure self.img has 4 channels (BGRA), converting from 3
        channels (BGR) if needed. A source with no alpha data gains a
        fully opaque one (255) - this does not create real transparency,
        only the channel itself."""
        if self.img is None:
            raise ValueError("Image not loaded.")
        if self.img.shape[2] == 3:
            self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)
        return self

    def draw_on(self, other_img: "Img", x: int, y: int) -> None:
        """Blend self onto other_img at pixel offset (x, y), respecting
        self's alpha channel if it has one."""
        if self.img is None or other_img.img is None:
            raise ValueError("Both images must be loaded before drawing.")

        if self.img.shape[2] != other_img.img.shape[2]:
            if self.img.shape[2] == 3 and other_img.img.shape[2] == 4:
                self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)
            elif self.img.shape[2] == 4 and other_img.img.shape[2] == 3:
                # self's real alpha must survive - upgrade other_img
                # instead of discarding self's transparency by downgrading it.
                other_img.img = cv2.cvtColor(other_img.img, cv2.COLOR_BGR2BGRA)

        h, w = self.img.shape[:2]
        H, W = other_img.img.shape[:2]

        if y + h > H or x + w > W:
            raise ValueError("Logo does not fit at the specified position.")

        roi = other_img.img[y:y + h, x:x + w]

        if self.img.shape[2] == 4:
            b, g, r, a = cv2.split(self.img)
            mask = a / 255.0
            for c in range(3):
                roi[..., c] = (1 - mask) * roi[..., c] + mask * self.img[..., c]
        else:
            other_img.img[y:y + h, x:x + w] = self.img

    def put_text(self, txt: str, x: int, y: int, font_size: float,
                 color: tuple[int, int, int, int] = (255, 255, 255, 255), thickness: int = 1) -> None:
        """Draw txt onto self.img at pixel position (x, y)."""
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(self.img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                    color, thickness, cv2.LINE_AA)

    def show(self) -> None:
        """Open a blocking window showing self.img until any key is pressed."""
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow("Image", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
