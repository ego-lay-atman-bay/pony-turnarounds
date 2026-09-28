from PIL import Image
import numpy as np

def crop_image(pil_image: Image.Image):
    # pil_image = Image.open(pil_image)
    if pil_image.mode != 'RGBA':
        pil_image = pil_image.convert('RGBA')
    np_array = np.array(pil_image)
    alpha_array =  np_array[:, :, 3]
    
    mask: np.typing.NDArray = alpha_array >= 25
    
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    if not rows.any():
        # fully transparent, nothing to crop
        return pil_image

    row_idx = np.where(rows)[0]
    col_idx = np.where(cols)[0]
    x0, x1 = row_idx[0], row_idx[-1] + 1
    y0, y1 = col_idx[0], col_idx[-1] + 1

    cropped_box = np_array[x0:x1, y0:y1]
    pil_image = Image.fromarray(cropped_box)
    return pil_image

if __name__ == "__main__":
    import argparse
    from glob import glob

    argparser = argparse.ArgumentParser(
        description = 'Crop images'
    )

    argparser.add_argument(
        'files',
        nargs = '+',
        help = 'Input file(s) to crop',
    )

    args = argparser.parse_args()

    files: list[str] = []

    for file in args.files:
        files.extend(glob(file))

    if len(files) == 0:
        print('no files to crop')
    
    for file in files:
        try:
            image = Image.open(file)
            image = crop_image(image)
            image.save(file)
        except Exception as e:
            print(e)

