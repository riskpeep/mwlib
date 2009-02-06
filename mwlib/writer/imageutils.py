#! /usr/bin/env python
#! -*- coding:utf-8 -*-

# Copyright (c) 2007, PediaPress GmbH
# See README.txt for additional licensing information.

from __future__ import division


from PIL import Image

class ImageUtils(object):

    def __init__(self, print_width,
                 print_height,
                 default_thumb_width,
                 img_min_res,
                 img_max_thumb_width,
                 img_max_thumb_height,
                 img_inline_scale_factor,
                 print_width_px
                 ):
        
        self.print_width = print_width
        self.print_height = print_height        
        self.default_thumb_width = default_thumb_width
        self.img_min_res = img_min_res
        self.img_max_thumb_width = img_max_thumb_width
        self.img_max_thumb_height = img_max_thumb_height
        self.img_inline_scale_factor = img_inline_scale_factor
        self.print_width_px = print_width_px
        
    def getImageSize(self, img_node, img_path, max_print_width=None, max_print_height=None):
        max_w = getattr(img_node, 'width', None)
        max_h = getattr(img_node, 'height', None)
        img = Image.open(img_path)
        px_w, px_h = img.size
        ar = px_w/px_h
        if max_h and max_w:
            if max_h*ar > max_w:
                max_h = max_w/ar
            elif max_w/ar > max_h:
                max_w = max_h*ar

        # check if thumb, then assign default width
        if getattr(img_node, 'thumb', None) or getattr(img_node, 'framed', None) or getattr(img_node, 'frameless', None):
            max_w = max_w or self.default_thumb_width
            img_node.floating = True
        if not max_w:
            max_w = min(self.print_width_px, px_w)
        max_w = min(self.print_width_px, max_w)
        scale = max_w / self.print_width_px
        img_print_width = self.print_width*scale
        
        if max_print_width and img_print_width > max_print_width:
            img_print_width = max_print_width
        if max_print_height:
            img_print_width = min(img_print_width, max_print_height*ar)

        # check min resolution
        resulting_dpi = px_w / img_print_width * 72
        if resulting_dpi < self.img_min_res:
            img_print_width = (resulting_dpi/self.img_min_res)*img_print_width

        # check size limits for floating images
        if getattr(img_node, 'floating', False):
            img_print_width = min(img_print_width, self.print_width*self.img_max_thumb_width, self.print_height*self.img_max_thumb_height*ar)

        if not max_print_width:
            max_print_width = self.print_width
        if img_node.isInline():
            if img_print_width < self.print_width/2: # scale "small" inline images
                img_print_width *= self.img_inline_scale_factor
            else: # FIXME: full width images are 12pt too wide - we need to check why
                img_print_width -= 12
        img_print_height = img_print_width/ar

        return (img_print_width, img_print_height)