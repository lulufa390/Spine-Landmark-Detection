import cv2 as cv
import numpy as np
import math
import copy

import cvui
import tkinter

import tkinter.messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename

import platform

sys = platform.system()



class SpineMarkingTools():

    def __init__(self, root):
        self.origin_image = None

        self.show_image = None

        self.points = []

        self.high_light_point = None

        self.height = None
        self.width = None

        self.scale = 1

        self.actual_height = None
        self.actual_width = None

        self.has_index = False

        self.main_window_name = "Spine Landmark Collection Tool"
        self.image_window_name = "Image View"

        self.main_frame = None
    
        self.tkinter_root = root
    
        self.threshold = [0.005]
    
        self.deleted_list = []

    def on_mouse_handler(self, event, x, y, flags, param):

        # process click new point and select highlight point first as button down
        if event == cv.EVENT_LBUTTONDOWN:

            float_x = (x / (self.actual_width - 1))
            float_y = (y / (self.actual_height - 1))

            is_select = False
            min_distance = np.inf
            for i, point in enumerate(self.points):
                distance = np.linalg.norm(np.array([float_x - point[0], float_y - point[1]]))
                if distance < self.threshold[0] and i not in self.deleted_list:
                    if distance < min_distance:
                        self.high_light_point = i
                        min_distance = distance
                    is_select = True

            if not is_select:
                if self.high_light_point is not None:
                    self.high_light_point = None
                else:
                    if len(self.deleted_list) > 0:
                        self.points[self.deleted_list[-1]] = (float_x, float_y)
                        self.deleted_list.pop()
                    else:
                        self.points.append((float_x, float_y))

        # if no button down but flag is true, then it is drag
        elif flags == cv.EVENT_FLAG_LBUTTON:
            float_x = (x / (self.actual_width - 1))
            float_y = (y / (self.actual_height - 1))
            if self.high_light_point is not None:
                self.points[self.high_light_point] = (float_x, float_y)


        elif sys == "Windows" and event == cv.EVENT_MOUSEWHEEL:

            if flags < 0:
                self.scale = max(self.scale - 0.03, 0.4)
            else:
                self.scale = self.scale + 0.03

            self.actual_height = int(self.height * self.scale)
            self.actual_width = int(self.width * self.scale)


    def draw_intersection(self, image, point, index):

        int_point = (int(point[0] * self.actual_width), int(point[1] * self.actual_height))

        size = int(self.actual_width / 80)

        p1 = (int(int_point[0] - size), int(int_point[1] - size))
        p2 = (int(int_point[0] - size), int(int_point[1] + size))
        p3 = (int(int_point[0] + size), int(int_point[1] - size))
        p4 = (int(int_point[0] + size), int(int_point[1] + size))

        cv.line(image, (p1[0], p1[1]), (p4[0], p4[1]), color=(255, 0, 0), thickness=1)
        cv.line(image, (p2[0], p2[1]), (p3[0], p3[1]), color=(255, 0, 0), thickness=1)

        if self.has_index:
            cv.putText(self.show_image, str(index + 1), (int_point[0], int_point[1]), cv.FONT_HERSHEY_COMPLEX, size / 6,
                       (0, 0, 255), 2)

    def keyboard(self, key):
        """
        :param key: keyboard input
        :param step: the adjustment step length
        """

        step_x = 1 / self.actual_width
        step_y = 1 / self.actual_height

        if self.high_light_point is not None:

            if key == 8:
                #del self.points[self.high_light_point]
                self.deleted_list.append(self.high_light_point)
                self.high_light_point = None

            elif key == 97:
                self.points[self.high_light_point] = \
                    (self.points[self.high_light_point][0] - step_x, self.points[self.high_light_point][1])

            elif key == 119:
                self.points[self.high_light_point] = \
                    (self.points[self.high_light_point][0], self.points[self.high_light_point][1] - step_y)

            elif key == 100:
                self.points[self.high_light_point] = \
                    (self.points[self.high_light_point][0] + step_x, self.points[self.high_light_point][1])

            elif key == 115:
                self.points[self.high_light_point] = \
                    (self.points[self.high_light_point][0], self.points[self.high_light_point][1] + step_y)

        if key == 113 and sys != "Windows":
            self.scale = max(self.scale - 0.03, 0.4)
            self.actual_height = int(self.height * self.scale)
            self.actual_width = int(self.width * self.scale)

        elif key == 101 and sys != "Windows":
            self.scale = self.scale + 0.03
            self.actual_height = int(self.height * self.scale)
            self.actual_width = int(self.width * self.scale)


    def load_image(self):
        # close tkinter default window as only use it to browse files

        filename = askopenfilename()

        try:
            self.origin_image = cv.imread(filename)
        except:
            tkinter.messagebox.showinfo("Warning", "Please Select Image File(.jpg/.png etc.)!")
            if self.is_window_open(self.image_window_name):
                cv.destroyWindow(self.image_window_name)
                cv.waitKey(1)
        else:
            if self.origin_image is None:
                tkinter.messagebox.showinfo("Warning", "Please Select Image File!")
                if self.is_window_open(self.image_window_name):
                    cv.destroyWindow(self.image_window_name)
                    cv.waitKey(1)

            else:

                cv.namedWindow(self.image_window_name)
                cvui.watch(self.image_window_name)

                self.height, self.width = self.origin_image.shape[0:2]
                
                self.scale = 1
                self.actual_height = int(self.height * self.scale)
                self.actual_width = int(self.width * self.scale)
                
                self.high_light_point = None

                self.points.clear()

                cv.setMouseCallback(self.image_window_name, self.on_mouse_handler)

    def save_to_txt(self):
        filename = asksaveasfilename(defaultextension=".txt", filetypes=[('text files', '.txt')])

        if len(filename) > 0:
            target_txt = open(filename, 'w')
            for point in self.points:
                string = str(point[0]) + "\t" + str(point[1]) + "\n"
                target_txt.write(string)
            target_txt.close()

        else:
            tkinter.messagebox.showinfo("Warning", "Please Enter A File Name!")

    def is_window_open(self, name):
        return cv.getWindowProperty(name, 0) != -1

    def read_txt(self):
        filename = askopenfilename()

        try:
            target_txt = open(filename, 'r')

        except:
            tkinter.messagebox.showinfo("Warning", "Please Select a txt File!")
        else:
            coordinates = np.array(target_txt.read().split()).reshape((-1, 2)).astype(np.float)
            self.points.clear()
            self.high_light_point = None
            for i in range(coordinates.shape[0]):
                self.points.append((coordinates[i, 0], coordinates[i, 1]))

    def run(self):

        self.main_frame = np.zeros((380, 400, 3), np.uint8)

        cv.namedWindow(self.main_window_name)
        cvui.init(self.main_window_name)

        while True:

            cvui.context(self.main_window_name)

            self.main_frame[:] = (49, 52, 49)

            cvui.beginColumn(self.main_frame, 50, 20, -1, -1, 10)

            cvui.text('Click to open an image')

            if cvui.button('Select Image'):
                self.load_image()
            
            cvui.text('Load a previously saved txt file to current image')

            if cvui.button("Read Txt file"):
                self.read_txt()

            cvui.text('Save to txt file')

            if cvui.button('Save'):
                self.save_to_txt()

            if cvui.button("Show/Hide Index"):
                self.has_index = not self.has_index
            
            if cvui.button("Clear All Points"):
                self.points.clear()
                self.high_light_point = None
            
            cvui.text('Max click distance to select one point')
            cvui.text('adjust smaller if you want to click two close points')
            cvui.trackbar(200, self.threshold, 0.000, 0.02, 2, '%.4Lf')

            cvui.endColumn()

            cvui.update(self.main_window_name)
            cv.imshow(self.main_window_name, self.main_frame)

            key = cv.waitKey(20)
            if key == 27 or not self.is_window_open(self.main_window_name):
                self.tkinter_root.destroy()
                break

            if self.is_window_open(self.image_window_name):

                cvui.context(self.image_window_name)

                self.show_image = cv.resize(self.origin_image, (self.actual_width, self.actual_height))

                for i, point in enumerate(self.points):
                    if i not in self.deleted_list:
                        self.draw_intersection(self.show_image, point, i)

                if self.high_light_point is not None:
                    point = self.points[self.high_light_point]
                    cv.circle(self.show_image, (int(point[0] * self.actual_width), int(point[1] * self.actual_height)),
                              5, (0, 255, 255), 1)

                # Fill the error window if a vibrant color
                # if self.image_window_flag:

                cvui.update(self.image_window_name)
                cv.imshow(self.image_window_name, self.show_image)

                self.keyboard(key)


if __name__ == '__main__':
    root = tkinter.Tk()
    root.withdraw()
    
    tool = SpineMarkingTools(root)
    tool.run()

    root.mainloop()
