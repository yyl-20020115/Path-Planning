# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 16:45:58 2023

@author: HJ
"""

# 深度优先搜索(Depth First Search, DFS)算法 
from typing import Union
from functools import lru_cache
from dataclasses import dataclass
from common import tic, toc, GridMap

# 地图读取
IMAGE_PATH = 'image.jpg'  # 原图路径
THRESH = 172  # 图片二值化阈值, 大于阈值的部分被置为255, 小于部分被置为0
HEIGHT = 350  # 地图高度
WIDTH = 600  # 地图宽度

MAP = GridMap(IMAGE_PATH, THRESH, HEIGHT, WIDTH)  # 栅格地图对象

# 起点终点     
START = (290, 270)  # 起点坐标 y轴向下为正
END = (298, 150)  # 终点坐标 y轴向下为正

""" ---------------------------- Depth First Search算法 ---------------------------- """


@dataclass(eq=False)
class Node:
    """节点"""

    x: int
    y: int
    parent: "Node" = None

    def __sub__(self, other) -> int:
        """计算节点与坐标的曼哈顿距离"""
        if isinstance(other, Node):
            return abs(self.x - other.x) + abs(self.y - other.y)
        elif isinstance(other, (tuple, list)):
            return abs(self.x - other[0]) + abs(self.y - other[1])
        raise ValueError("other必须为坐标或Node")

    def __add__(self, other: Union[tuple, list]) -> "Node":
        """生成新节点"""
        x = self.x + other[0]
        y = self.y + other[1]

        return Node(x, y, self)

    def __eq__(self, other):
        """坐标x,y比较 -> node in close_list"""
        if isinstance(other, Node):
            return self.x == other.x and self.y == other.y
        elif isinstance(other, (tuple, list)):
            return self.x == other[0] and self.y == other[1]
        return False

    def __hash__(self) -> int:
        """使可变对象可hash, 能放入set中"""
        return hash((self.x, self.y))  # tuple 可 hash
        # data in set 时间复杂度为 O(1), 但 data必须可hash
        # data in list 时间复杂度 O(n)


# NOTE 深度优先先进后出, 用列表即可


# 深度优先搜索算法
class DFS:
    """DFS算法"""

    def __init__(
            self,
            start_pos=START,
            end_pos=END,
            map_array=MAP.map_array,
            move_step=5,
            move_direction=8,
    ):
        """DFS算法

        Parameters
        ----------
        start_pos : tuple/list
            起点坐标
        end_pos : tuple/list
            终点坐标
        map_array : ndarray
            二值化地图, 0表示障碍物, 255表示空白, H*W维
        move_step : int
            移动步数, 默认5
        move_direction : int (8 or 4)
            移动方向, 默认8个方向
        """
        # 网格化地图
        self.path_list = None
        self.open_list = None
        self.close_set = None
        self.move_direction = None
        self.move_step = None
        self.__reset_flag = None
        self.map_array = map_array  # H * W

        self.width = self.map_array.shape[1]
        self.height = self.map_array.shape[0]

        # 起点终点
        self.start = Node(*start_pos)  # 初始位置
        self.end = Node(*end_pos)  # 结束位置

        # Error Check
        if not self._in_map(self.start) or not self._in_map(self.end):
            raise ValueError(f"x坐标范围0~{self.width - 1}, y坐标范围0~{self.height - 1}")
        if self._is_collided(self.start):
            raise ValueError(f"起点x坐标或y坐标在障碍物上")
        if self._is_collided(self.end):
            raise ValueError(f"终点x坐标或y坐标在障碍物上")

        # 算法初始化
        self.reset(move_step, move_direction)

    def reset(self, move_step=3, move_direction=8):
        """重置算法"""
        self.__reset_flag = False
        self.move_step = move_step  # 移动步长(搜索后期会减小)
        self.move_direction = move_direction  # 移动方向 8 个
        self.close_set = set()  # 存储已经走过的位置及其G值
        self.open_list = []  # 存储当前位置周围可行的位置及其F值
        self.path_list = []  # 存储路径(CloseList里的数据无序)

    def search(self):
        """搜索路径"""
        return self.__call__()

    def _in_map(self, node: Node):
        """点是否在网格地图中"""
        return (0 <= node.x < self.width) and (0 <= node.y < self.height)  # 右边不能取等!!!

    def _is_collided(self, node: Node):
        """点是否和障碍物碰撞"""
        return self.map_array[node.y, node.x] == 0

    def _move(self):
        """移动点"""

        @lru_cache(maxsize=3)  # 避免参数相同时重复计算
        def _move(move_step: int, move_direction: int):
            move = [
                (0, move_step),  # 上
                (0, -move_step),  # 下
                (-move_step, 0),  # 左
                (move_step, 0),  # 右
                (move_step, move_step),  # 右上
                (move_step, -move_step),  # 右下
                (-move_step, move_step),  # 左上
                (-move_step, -move_step),  # 左下
            ]
            return move[0:move_direction]  # 坐标增量

        return _move(self.move_step, self.move_direction)[::-1]  # 后入先出, 斜着搜索太慢, 把直的放后面

    def _update_open_list(self, curr: Node):
        """open_list添加可行点"""
        for add in self._move():
            # 更新节点
            next_ = curr + add  # x、y、cost、parent都更新了

            # 新位置是否在地图外边
            if not self._in_map(next_):
                continue
            # 新位置是否碰到障碍物
            if self._is_collided(next_):
                continue
            # 新位置是否在 CloseList 和 OpenList 中
            if next_ in self.close_set or next_ in self.open_list:
                continue

            # open-list添加结点
            self.open_list.append(next_)

            # 当剩余距离小时, 走慢一点
            if (next_ - self.end) < 20:
                self.move_step = 1

    def __call__(self):
        """DFS路径搜索"""
        assert not self.__reset_flag, "call之前需要reset"
        print("搜索中\n")

        # 初始化 OpenList
        self.open_list.append(self.start)
        curr = None
        # 正向搜索节点
        tic()
        while self.open_list:
            # 弹出 OpenList 最后的节点
            curr = self.open_list.pop()
            # 更新 OpenList
            self._update_open_list(curr)
            # 更新 CloseList
            self.close_set.add(curr)
            # 结束迭代
            if curr == self.end:
                break
        print("路径搜索完成\n")
        toc()

        # 节点组合成路径
        while curr.parent is not None:
            self.path_list.append(curr)
            curr = curr.parent
        self.path_list.reverse()

        # 需要重置
        self.__reset_flag = True

        return self.path_list


# debug
if __name__ == '__main__':
    p = DFS()()
    MAP.show_path(p)
