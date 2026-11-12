import Foundation
import Vision
let url=URL(fileURLWithPath:CommandLine.arguments[1])
let request=VNDetectBarcodesRequest()
request.symbologies=[.qr]
try VNImageRequestHandler(url:url).perform([request])
let values=(request.results ?? []).compactMap{$0.payloadStringValue}
let expected="https://ai.lucasacademy.org/courses/zero-and-one/"
guard values.contains(expected) else {
    fputs("Course QR missing from final movie frame\n",stderr)
    exit(1)
}
print("QR verified: \(expected)")
