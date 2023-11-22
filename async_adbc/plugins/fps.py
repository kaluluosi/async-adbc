from async_adbc.plugin import Plugin
from typing import List, Optional
from pydantic import BaseModel, Field


class SurfaceNotFoundError(Exception):
    ...


class FpsStat(BaseModel):
    fps: float = 0
    jank: float = 0
    big_jank: float = 0
    frametimes: List[float] = Field(default=list)  # type: ignore


class FpsPlugin(Plugin):
    async def get_surface_view(self, package_name: str) -> Optional[str]:
        result: str = await self._device.shell(
            f'dumpsys SurfaceFlinger --list|grep "{package_name}"'
        )

        results = result.split("\n")

        # 由上到下扫描出最后一个SurfaceView
        top_surface_view = None
        surface_views = filter(lambda txt: txt.startswith("SurfaceView"), results)
        surface_views = list(surface_views)
        if surface_views:
            top_surface_view = surface_views[-1]

        # 找出包含app_name的SurfaceView
        top_app_surface_view = None
        app_surface_views = filter(
            lambda txt: package_name in txt and txt.startswith("SurfaceView"),
            results,
        )
        app_surface_views = list(app_surface_views)
        if app_surface_views:
            top_app_surface_view = app_surface_views[-1]

        target_surface_view = top_app_surface_view or top_surface_view

        return target_surface_view.strip() if target_surface_view else None

    async def stat(self, package_name: str) -> FpsStat:
        """
        采样

        Args:
            package_name (str): 包名

        Returns:
            FpsStat: 帧率数据
        """

        data = FpsStat(fps=0, jank=0, big_jank=0, frametimes=[])

        surface_view = await self.get_surface_view(package_name)

        if not surface_view:
            return data

        result: str = await self._device.shell(
            f'dumpsys SurfaceFlinger --latency "{surface_view}"'
        )
        refresh_period, data_table = self._parse_data(result)
        if not data_table:
            return data

        fps = self._calc_fps(data_table, refresh_period)
        jank, big_jank, frametimes = self._calc_jank(data_table, refresh_period)

        return FpsStat(fps=fps, jank=jank, big_jank=big_jank, frametimes=frametimes)

    def _parse_data(self, result: str):
        lines = result.strip().split("\n")
        refresh_period = float(lines[0])

        data = []
        if len(lines) > 1:
            for line in lines[1:]:
                line_data = [float(v) for v in line.split("\t")]
                data.append(line_data)
        data = list(filter(lambda v: sum(v) > 0, data))

        return refresh_period, data

    def _calc_jank(self, data_table, refresh_period):
        jank_count = 0.0
        big_jank_count = 0.0

        # 计算帧间隔，转为ms
        frametimes: list[float] = [
            round((data_table[i + 1][0] - data_table[i][0]) / pow(10, 6), 2)
            for i in range(len(data_table) - 1)
        ]

        for i in range(3, len(frametimes)):
            pre_three_avg = (
                frametimes[i - 1] + frametimes[i - 2] + frametimes[i - 3]
            ) / 3
            cur_frametime = frametimes[i]
            if cur_frametime > 2 * pre_three_avg:
                if cur_frametime > 83.33:
                    jank_count += 1

                if cur_frametime > 125:
                    big_jank_count += 1

        return jank_count, big_jank_count, frametimes

    def _calc_fps(self, data_table, refresh_period):
        if refresh_period < 0:
            return -1.0

        frame_count = len(data_table)

        if frame_count == 0:
            return 0
        elif frame_count == 1:
            return 1

        start_time = data_table[0][0]
        end_time = data_table[-1][0]

        duration = end_time - start_time
        # pow(10,9)是 1000000000 ，用来把纳秒转秒
        if duration <= 0:  # 可能是0
            return 1

        return frame_count * pow(10, 9) / duration
