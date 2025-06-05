'''
© 2025, ams-OSRAM AG
'''


from abc import ABC
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QPixmap
from PyQt5.QtWidgets import QLabel, QStatusBar, QWidget
import os

class Style(ABC):

    # COLORS FROM THE ams OSRAM brand guideline
    # see https://osram.sharepoint.com/:b:/r/sites/news-center/Shared%20Documents/amsOSRAM_Brand-Guideline.pdf (17 March 2022)
    # PRIMARY PALETTE
    # Our core color palette helps identify ams OSRAM and maintain brand recognition across all communications.
    # A minimum of 2 core colors should always be used in a single application.
    # Orange is mandatory in some form either through solid background color, surface texture,
    # Visual Corporate Identity, headline copy or iconography.
    # Note: the _70 and _30 variants are taken from the guide for mobile applications
    COLOR_PRIMARY_ORANGE = QColor(253, 80, 0)
    COLOR_PRIMARY_ORANGE_70 = QColor(254, 132, 76)
    COLOR_PRIMARY_ORANGE_30 = QColor(254, 202, 178)
    COLOR_PRIMARY_GREY = QColor(70, 85, 95)
    COLOR_PRIMARY_GREY_70 = QColor(125, 136, 143)
    COLOR_PRIMARY_GREY_30 = QColor(199, 204, 207)
    COLOR_PRIMARY_CREAM = QColor(253, 246, 241)
    # SECONDARY PALETTE
    # Blue should be used sparingly for highlighting small assets such as graphs, buttons or icons
    # but never in large areas or for headlines/body copy.
    COLOR_SECONDARY_BLUE = QColor(0, 173, 253)
    # TYPE PALETTE
    # Dark grey is for typography as it is more harmonious with our color palette than pure black and should always
    # be used in all typographic executions. It should never be applied for any other use.
    # On occasions we use Dark Blue when we want to create standout headlines, sublines or to highlight words/short
    # sentences in body copy.
    # Dark Blue is used as it conforms to the Web Content Accessibility Guidelines for AA contrast accessibility. (See Typography section for more detail.)
    COLOR_TYPE_DARK_GREY = QColor(29, 37, 45)
    COLOR_TYPE_DARK_BLUE = QColor(0, 112, 207)
    # ACCENT PALETTE
    # Our extended accent palette is available if additional colors are required for functional purposes such as complex infographics, charts or graphs that require five or more colors for both digital and print.
    # Always use mid range set first then further options can be made using the lighter and darker tones.
    COLOR_ACCENT_PURPLE = QColor(170, 0, 255)
    COLOR_ACCENT_DARK_PURPLE = QColor(114, 0, 202)
    COLOR_ACCENT_LIGHT_PURPLE = QColor(226, 84, 255)
    COLOR_ACCENT_BLUE = QColor(0, 173, 253)
    COLOR_ACCENT_DARK_BLUE = QColor(0, 112, 207)
    COLOR_ACCENT_LIGHT_BLUE = QColor(105, 223, 255)
    COLOR_ACCENT_GREEN = QColor(0, 230, 118)
    COLOR_ACCENT_DARK_GREEN = QColor(0, 178, 73)
    COLOR_ACCENT_LIGHT_GREEN = QColor(102, 255, 167)
    COLOR_ACCENT_YELLOW = QColor(255, 234, 0)
    COLOR_ACCENT_DARK_YELLOW = QColor(197, 158, 0)
    COLOR_ACCENT_LIGHT_YELLOW = QColor(255, 255, 86)
    COLOR_ACCENT_RED = QColor(255, 0, 85)
    COLOR_ACCENT_DARK_RED = QColor(196, 0, 45)
    COLOR_ACCENT_LIGHT_RED = QColor(255, 91, 129)

    # CUSTOM COLORS ("inspired" by the ams OSRAM brand guideline)
    COLOR_PURPLISH_GREY_20 = QColor(73, 78, 103)  # COLOR_ACCENT_DARK_PURPLE @ opacity 20 on top of COLOR_PRIMARY_GREY
    COLOR_BLUISH_GREY_20 = QColor(64, 87, 103)  # COLOR_ACCENT_DARK_BLUE @ opacity 20 on top of COLOR_PRIMARY_GREY
    COLOR_GREENISH_GREY_20 = QColor(64, 92, 93)  # COLOR_ACCENT_DARK_GREEN @ opacity 20 on top of COLOR_PRIMARY_GREY
    COLOR_YELLOWISH_GREY_20 = QColor(79, 90, 87)  # COLOR_ACCENT_DARK_YELLOW @ opacity 20 on top of COLOR_PRIMARY_GREY
    COLOR_REDDISH_GREY_20 = QColor(79, 78, 91)  # COLOR_ACCENT_DARK_RED @ opacity 20 on top of COLOR_PRIMARY_GREY
    
    # Qt's platform independent desktop style "Fusion"
    STYLE_NAME = "Fusion"

    # Font: use the font from the ams OSRAM guidelines (ttf embedded since not installed by default)
    # Note: this is slightly different from Koala, maybe due to PyQt?
    FONT_NAME = "Lexend Light"
    FONT_FAMILY = "Lexend"
    FONT_STYLE = "Light"
    FONT_FILE = "/fonts/Lexend/Lexend-Light.ttf"
    FONT_SIZE = 12

    # Default palette
    default_palette = QPalette()
    default_palette.setColor(QPalette.Window, COLOR_PRIMARY_GREY)
    default_palette.setColor(QPalette.Base, default_palette.color(QPalette.Window))
    default_palette.setColor(QPalette.Button, default_palette.color(QPalette.Window))
    default_palette.setColor(QPalette.Highlight, Qt.white)
    default_palette.setColor(QPalette.Text, Qt.white)
    default_palette.setColor(QPalette.ButtonText, default_palette.color(QPalette.Text))
    default_palette.setColor(QPalette.WindowText, default_palette.color(QPalette.Text))
    default_palette.setColor(QPalette.HighlightedText, COLOR_PRIMARY_GREY)
    default_palette.setColor(QPalette.Disabled, QPalette.Text, COLOR_PRIMARY_GREY_70)
    default_palette.setColor(QPalette.Disabled, QPalette.WindowText, default_palette.color(QPalette.Disabled, QPalette.Text))
    default_palette.setColor(QPalette.Disabled, QPalette.ButtonText, default_palette.color(QPalette.Disabled, QPalette.Text))
    default_palette.setColor(QPalette.Link, default_palette.color(QPalette.Text))
    default_palette.setColor(QPalette.LinkVisited, default_palette.color(QPalette.Text))
   
    @staticmethod
    def create_status_bar(version):
        # Create status bar
        status_bar = QStatusBar()

        # Add space between temporally message and the permanent version
        space_widget = QWidget()
        # 13px is chosen to have the same spacing between the right of the version and the left of the "ams OSRAM" VCI
        space_widget.setFixedWidth(13)
        status_bar.addPermanentWidget(space_widget)

        # Version label
        status_bar.addPermanentWidget(QLabel(f"version {version}"))

        # Add VCI (company logo)
        # The image consists of the Visual Corporate Identity (VCI, the "logo" consisting of both ams and OSRAM company logo's)
        # and a protection zone around it (the "M" in the style definition). The minimum size allowed by the style definition is
        # 140px width and 16px height for VCI only, or 170px width and 46px height for the VCI with protection zone around it
        # (protection zone is 15px when VCI is at minimum size). The image used here is the SVG file resized by Raphael Relinger
        # from Marcom using Photoshop".
        company_logo_label = QLabel()
        company_logo_pixmap = QPixmap(os.path.dirname(__file__) + '/artwork/ams_OSRAM_VCI_Landscape_OnGrey_RGB_170x46.png')
        company_logo_label.setPixmap(company_logo_pixmap)
        status_bar.addPermanentWidget(company_logo_label)

        # Styling
        border_size = 1
        status_bar.setStyleSheet(
            f'QStatusBar {{border-top: {border_size}px solid {Style.COLOR_PRIMARY_ORANGE.name()}}}')
        # Status bar height: there seems to be an unremovable space (or border) of 2px above and below the permanent
        # widgets. Take this into account for seting a fixed height, otherwise the VCI will be scaled which is not allowed.
        status_bar.setFixedHeight(border_size + 2*2 + company_logo_pixmap.height())
        status_bar.setSizeGripEnabled(False)

        return status_bar


