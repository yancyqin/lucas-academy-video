// Decode the actually rendered frame, including quiet zone and display scaling.
import Foundation
import Vision
let url=URL(fileURLWithPath:CommandLine.arguments[1])
let request=VNDetectBarcodesRequest()
request.symbologies=[.qr]
try VNImageRequestHandler(url:url).perform([request])
let values=(request.results ?? []).compactMap{$0.payloadStringValue}
guard values.contains("https://ai.lucasacademy.org/") else {
    fputs("QR URL missing from rendered frame\n",stderr)
    exit(1)
}
print("QR verified: https://ai.lucasacademy.org/")
