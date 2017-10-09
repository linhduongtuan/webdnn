from typing import Tuple, Optional

from webdnn.graph.axis import Axis
from webdnn.graph.operator import Operator
from webdnn.graph.operators.attributes.tensorwise import Tensorwise
from webdnn.graph.operators.util import IntOrTuple, to_tuple
from webdnn.graph.order import OrderNHWC, OrderNCHW
from webdnn.graph.placeholder import Placeholder
from webdnn.graph.variable import Variable


class Deconvolution2D(Operator):
    """Deconvolution2D(name, ksize, stride, padding)

    Spatial deconvolution operator.

    Args:
        name (str): Operator name.
        ksize (int or tuple of int): Kernel size.
        stride (int or tuple of int): Stride size.
        padding (int or tuple of int): Padding size.

    Signature
        .. code::

            y, = op(x, w)

        - **x** - Input variables. It must has 4 axes, :obj:`~webdnn.Axis.N`, :obj:`~webdnn.Axis.C`,
          :obj:`~webdnn.Axis.H`, and :obj:`~webdnn.Axis.W`.
        - **w** - Kernel variable. It must has :obj:`~webdnn.graph.axis.Axis.N`, :obj:`~webdnn.Axis.C`,
          :obj:`~webdnn.Axis.H`, :obj:`~webdnn.Axis.W`. Its size of :obj:`~webdnn.Axis.H` and
          :obj:`~webdnn.Axis.W` must be same as kernel size. Its size of :obj:`~webdnn.Axis.C` must be same as
          :code:`x`.
        - **y** - Output variable. Its order is same as :code:`x`.
    """

    def __init__(self, name: Optional[str], ksize: IntOrTuple, stride: IntOrTuple, padding: IntOrTuple):
        super().__init__(name)
        self.parameters["ksize"] = to_tuple(ksize)
        self.parameters["stride"] = to_tuple(stride)
        self.parameters["padding"] = to_tuple(padding)
        self.attributes.add(Tensorwise(self, Axis.N))

    def __call__(self, x: Variable, w: Variable):
        self.append_input("x", x)
        self.append_input("w", w)
        return self.exec()

    def exec(self):
        x = self.inputs["x"]
        w = self.inputs["w"]

        assert x.order.check_same_axes(OrderNCHW), \
            "Input variable of Deconvolution2D must have N, C, H, and W axes.: " \
            f"x.order.axes={x.order.axes}"

        assert w.order.check_same_axes(OrderNCHW), \
            "Kernel variable of Deconvolution2D must have N, C, H, and W axes.: " \
            f"w.order.axes={w.order.axes}"

        if Placeholder.check_resolved(w.shape_dict[Axis.H]) and Placeholder.check_resolved(w.shape_dict[Axis.W]):
            assert (w.shape_dict[Axis.H], w.shape_dict[Axis.W]) == self.ksize, \
                "Kernel variable of Deconvolution2D must be same spatial size as ksize parameter: " \
                f"w.shape_dict[Axis.H]={w.shape_dict[Axis.H]}, " \
                f"w.shape_dict[Axis.W]={w.shape_dict[Axis.W]}, " \
                f"self.ksize={self.ksize}"

        if Placeholder.check_resolved(w.shape_dict[Axis.C]) and Placeholder.check_resolved(x.shape_dict[Axis.C]):
            assert w.shape_dict[Axis.C] == x.shape_dict[Axis.C], \
                "Input and Kernel variables of Deconvolution2D must be same channel size: " \
                f"x.shape_dict[Axis.C]={x.shape_dict[Axis.C]}, " \
                f"w.shape_dict[Axis.C]={w.shape_dict[Axis.C]}"

        N = x.shape_dict[Axis.N]
        H2 = (x.shape_dict[Axis.H] - 1) * self.SH - 2 * self.PH + self.KH
        W2 = (x.shape_dict[Axis.W] - 1) * self.SW - 2 * self.PW + self.KW
        C2 = w.shape_dict[Axis.N]

        y = Variable([N, H2, W2, C2], OrderNHWC)
        y.change_order(x.order)  # output same order as input to preserve following reshape semantics

        self.append_output("y", y)
        return y,

    @property
    def ksize(self) -> Tuple[int, int]:
        return self.parameters["ksize"]

    @property
    def stride(self) -> Tuple[int, int]:
        return self.parameters["stride"]

    @property
    def padding(self) -> Tuple[int, int]:
        return self.parameters["padding"]

    @property
    def KH(self) -> int:
        return self.ksize[0]

    @property
    def KW(self) -> int:
        return self.ksize[1]

    @property
    def SH(self) -> int:
        return self.stride[0]

    @property
    def SW(self) -> int:
        return self.stride[1]

    @property
    def PH(self) -> int:
        return self.padding[0]

    @property
    def PW(self) -> int:
        return self.padding[1]
