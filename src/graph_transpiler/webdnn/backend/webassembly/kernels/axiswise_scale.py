from typing import List

from webdnn.backend.code_generator.allocator import MemoryLayout
from webdnn.backend.code_generator.injectors.kernel_name_injector import KernelNameInjector
from webdnn.backend.code_generator.injectors.buffer_injector import BufferInjector
from webdnn.backend.webassembly.kernel import Kernel
from webdnn.graph.axis import Axis
from webdnn.graph.operators.axiswise_scale import AxiswiseScale
from webdnn.graph.order import OrderNHWC, OrderNC, OrderHWNC

template = """
void %%FUNC_NAME%%(const int * %%META_BUFFER%%)
{
    const float *X = %%LOAD_BUFFER(axiswise_scale_X)%%;
    float *Y = %%LOAD_BUFFER(axiswise_scale_Y)%%;
    const float *S = %%LOAD_BUFFER(axiswise_scale_S)%%;
    const int N = %%LOAD_BUFFER(axiswise_scale_N)%%;
    const int C = %%LOAD_BUFFER(axiswise_scale_C)%%;
  
    for (int gid = 0; gid < N; gid += 1) {
        int c = gid % C;
        float result = X[gid] * S[c];

        Y[gid] = result;
    }
}
"""


def axiswise_scale(op: AxiswiseScale, memory_layout: MemoryLayout) -> List[Kernel]:
    x = memory_layout[op.inputs["x"]]
    s = memory_layout[op.inputs["s"]]
    y = memory_layout[op.outputs["y"]]

    assert x.variable.order == OrderNC or x.variable.order == OrderNHWC or x.variable.order == OrderHWNC
    assert y.variable.order == OrderNC or y.variable.order == OrderNHWC or y.variable.order == OrderHWNC
    assert op.parameters["axis"] == Axis.C, "[Webassembly] AxiswiseScale supports only channelwise bias."

    buffer_injector = BufferInjector()
    buffer_injector.register({
        "axiswise_scale_X": x,
        "axiswise_scale_Y": y,
        "axiswise_scale_S": s,
        "axiswise_scale_N": y.variable.size,
        "axiswise_scale_C": y.variable.shape_dict[Axis.C],
    })

    name_injector = KernelNameInjector(op)

    source = template
    source = buffer_injector.inject(source)
    source = name_injector.inject(source)

    kernel = Kernel(
        {name_injector.name: source},
        name_injector.name,
        buffer_injector.buffer,
        buffer_injector.unresolved_value_list
    )

    return [kernel]
