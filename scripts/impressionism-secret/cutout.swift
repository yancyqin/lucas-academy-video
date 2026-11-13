import Foundation
import Vision
import CoreImage
import ImageIO
import UniformTypeIdentifiers

// Usage: cutout <in> <out.png> — Vision foreground subject lift; keeps the original pixels and frame size.
let args = CommandLine.arguments
guard args.count == 3 else { print("usage: cutout in out"); exit(2) }
let inURL = URL(fileURLWithPath: args[1]), outURL = URL(fileURLWithPath: args[2])
guard let src = CGImageSourceCreateWithURL(inURL as CFURL, nil),
      let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("cannot read"); exit(1) }
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
let req = VNGenerateForegroundInstanceMaskRequest()
do { try handler.perform([req]) } catch { print("vision error \(error)"); exit(1) }
guard let obs = req.results?.first else { print("no subject"); exit(3) }
let masked = try obs.generateMaskedImage(ofInstances: obs.allInstances, from: handler, croppedToInstancesExtent: false)
let ci = CIImage(cvPixelBuffer: masked)
let ctx = CIContext()
guard let outCG = ctx.createCGImage(ci, from: ci.extent),
      let dest = CGImageDestinationCreateWithURL(outURL as CFURL, UTType.png.identifier as CFString, 1, nil) else { exit(1) }
CGImageDestinationAddImage(dest, outCG, nil)
CGImageDestinationFinalize(dest)
print("ok \(Int(ci.extent.width))x\(Int(ci.extent.height)) instances=\(obs.allInstances.count)")
