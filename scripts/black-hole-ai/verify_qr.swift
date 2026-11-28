// Decode a QR code from an image with macOS Vision and require an exact payload (as scripts/family-ai-lab-0{1,2}/verify_qr.swift).
//   swift scripts/black-hole-ai/verify_qr.swift FRAME.png https://is.lucasacademy.org
// The film's end card is checked on a frame decoded from the delivered MP4, at 1080p and scaled to 720p.
import Foundation
import Vision
let url=URL(fileURLWithPath:CommandLine.arguments[1])
let expected=CommandLine.arguments[2]
let request=VNDetectBarcodesRequest()
request.symbologies=[.qr]
try VNImageRequestHandler(url:url).perform([request])
let values=(request.results ?? []).compactMap{$0.payloadStringValue}
print("decoded: \(values)")
guard values.contains(expected) else { fputs("QR \(expected) not found\n",stderr); exit(1) }
print("QR verified: \(expected)")
