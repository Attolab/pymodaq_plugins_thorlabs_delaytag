from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pylablib.devices import Thorlabs

from pymodaq_plugins_thorlabs.daq_viewer_plugins.plugins_2D.daq_2Dviewer_Thorlabs_TSI import DAQ_2DViewer_Thorlabs_TSI


from qtpy import QtWidgets, QtCore
import numpy as np
from time import perf_counter


class DAQ_2DViewer_Thorlabs_TSI_DelayTag(DAQ_2DViewer_Thorlabs_TSI):
    """
    Little modification to use thorlabs camera as delay tagging
    """

    params = DAQ_2DViewer_Thorlabs_TSI.params + [
        {'title': 'Delay Tagging', 'name': 'delay_opts', 'type': 'group', 'children':
            [{'title': 'Acquisition Time (ms)', 'name': 'acq_time', 'type': 'int', 'value': 1},
             {'title': 'Enable tagging', 'name': 'tag_on', 'type': 'bool', 'value': False}]
         }]

    acq_start_time = None
    data_tag = []

    def grab_data(self, Naverage=1, **kwargs):
        if self.settings.child('delay_opts','tag_on').value():
            self.acq_start_time = perf_counter()  # Save time at which acquisition start

        super().grab_data(Naverage=1, **kwargs)

    def emit_data(self):
        try:
            if not self.settings.child('delay_opts', 'tag_on').value():
                super().emit_data()     # if we are in normal mode, just do as usual

            else:
                # In delay tag mode, we sum data
                frame = self.controller.read_newest_image()
                if frame is not None:
                    self.data_tag.append(np.sum(frame, axis=0))

                # We stack fringe images till we reach "acq_time"
                emit_time = perf_counter()
                # Acq_time is reached
                if emit_time - self.acq_start_time > self.settings.child('delay_opts', 'acq_time').value()/1000:
                    # Emit data
                    self.data_grabed_signal.emit([DataFromPlugins(name='Thorlabs Camera',
                                                                  data=[np.asarray(self.data_tag)],
                                                                  dim='Data2D',
                                                                  labels=[f'Delay tag'])])
                    # Empty data array
                    self.data_tag = []
                    # Reset counter
                    self.acq_start_time = perf_counter()
                else:
                    self.callback_signal.emit()  # Wait for next acquisition


                    # To make sure that timed events are executed in continuous grab mode
                QtWidgets.QApplication.processEvents()

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), 'log']))

if __name__ == '__main__':
    main(__file__, init=False)
