import board
import displayio
import constants
import fonts
from adafruit_display_text import label

class MenuScreen:

    PADDING_HEADER = 4
    PADDING_ITEM = 5
    ITEMS_PER_SCREEN = 3

    def __init__(self):
        self.group = displayio.Group()

        # Setup color palette
        color_to_index = {k:i for (i,k) in enumerate(constants.COLOR_TO_RGB)}
        self.palette = displayio.Palette(len(constants.COLOR_TO_RGB))
        for i, palette_tuple in enumerate(constants.COLOR_TO_RGB.items()):
            self.palette[i] = palette_tuple[1]   

        # Create tile grid
        self.bitmap = displayio.Bitmap( 
                board.DISPLAY.width, 
                board.DISPLAY.height, 
                len(constants.COLOR_TO_RGB)
                )
        self.bitmap.fill(color_to_index['black'])
        self.tile_grid = displayio.TileGrid(self.bitmap,pixel_shader=self.palette)
        font_scale = 1

        # Create header text label
        header_str = 'Menu'
        self.header_label = label.Label(
                fonts.font_14pt, 
                text = header_str, 
                color = constants.COLOR_TO_RGB['white'], 
                scale = font_scale,
                anchor_point = (0.5, 1.0)
                )
        header_x = board.DISPLAY.width//2 
        header_y = self.header_label.bounding_box[3] + self.PADDING_HEADER 
        self.header_label.anchored_position = header_x, header_y

        # Create line under menu
        menu_line_y0 = header_y + self.PADDING_HEADER 
        for x_position in range(board.DISPLAY.width):
            self.bitmap[x_position, menu_line_y0] = color_to_index['gray']

        # Fixed for the 160x128 PyBadge display. Avoids allocating a temporary
        # label only to measure its height.
        label_dy = 20
        self.items_per_screen = self.ITEMS_PER_SCREEN

        self.item_labels = []
        for i in range(self.items_per_screen): 
            pos_x = 2
            pos_y = menu_line_y0 + (i+1)*label_dy 
            label_tmp = label.Label(
                     fonts.font_10pt,
                     text = '',
                     color = constants.COLOR_TO_RGB['white'],
                     scale = font_scale,
                     anchor_point = (0.0, 1.0),
                     anchored_position = (pos_x, pos_y),
                     padding_right = 160
                     )
            self.item_labels.append(label_tmp)

        # Ceate display group and add items to it
        self.group.append(self.tile_grid)
        self.group.append(self.header_label)
        for item_label in self.item_labels:
            self.group.append(item_label)

        self.set_curr_item(0)

    def set_menu_items(self, text_list):
        for item_label, item_text in zip(self.item_labels, text_list):
            item_label.text = item_text 

    def set_curr_item(self, num):
        for i, item_label in enumerate(self.item_labels):
            if i==num:
                item_label.color = constants.COLOR_TO_RGB['black']
                item_label.background_color = constants.COLOR_TO_RGB['orange']
            else:
                item_label.color = constants.COLOR_TO_RGB['white']
                item_label.background_color = constants.COLOR_TO_RGB['black']

    def show(self):
        board.DISPLAY.root_group = self.group
