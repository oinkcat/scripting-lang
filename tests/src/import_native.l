# Import native module test
import native math

angle = math.Rand() * math.PI * 2

emit "Angle: ${angle}"
emit "Sine: ${math.Sin(angle)}"
emit "Cosine: ${math.Cos(angle)}"
