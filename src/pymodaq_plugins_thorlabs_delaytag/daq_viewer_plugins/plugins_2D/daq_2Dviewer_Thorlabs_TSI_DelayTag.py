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
            [{'title': 'Number of samples', 'name': 'acq_number', 'type': 'int', 'value': 10},
             {'title': 'Enable tagging', 'name': 'tag_on', 'type': 'bool', 'value': False},
             {'title': 'Acquis. time (ms)', 'name': 'acq_time', 'type': 'float', 'value': 0., 'readonly': True}]
         }]

    acq_counter = 0
    acq_time = 0.
    data_tag = []

    def grab_data(self, Naverage=1, **kwargs):
        if self.settings.child('delay_opts','tag_on').value():
            self.acq_counter = 0
            self.acq_time = perf_counter() # Save time at which acquisition start
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

                # We stack fringe images till we reach the sample number
                self.acq_counter += 1

                # Acq number is reached
                if self.acq_counter >= self.settings.child('delay_opts', 'acq_number').value():
                    # Emit data
                    self.data_grabed_signal.emit([DataFromPlugins(name='Thorlabs Camera',
                                                                  data=[np.asarray(self.data_tag)],
                                                                  dim='Data2D',
                                                                  labels=[f'Delay tag'])])
                    self.settings.child('delay_opts', 'acq_time').setValue(round((perf_counter()-self.acq_time)*1000,1))

                    # Empty data array
                    self.data_tag = []
                    # Reset counter
                    self.acq_counter = 0
                    self.acq_time = perf_counter()
                else:
                    self.callback_signal.emit()  # Wait for next acquisition

                    # To make sure that timed events are executed in continuous grab mode
                QtWidgets.QApplication.processEvents()

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), 'log']))

if __name__ == '__main__':
    main(__file__, init=False)
