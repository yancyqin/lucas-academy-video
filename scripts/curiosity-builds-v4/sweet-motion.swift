import CoreGraphics
import Foundation

// Only orbit the already-open 3D preview. Do not reset, edit, or save the home.
let a = CGPoint(x: 1300, y: 1080)
let b = CGPoint(x: 1385, y: 1065)
let from = CommandLine.arguments.contains("--reverse") ? b : a
let to = CommandLine.arguments.contains("--reverse") ? a : b
CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: from, mouseButton: .left)?.post(tap: .cghidEventTap)
usleep(150_000)
CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: from, mouseButton: .left)?.post(tap: .cghidEventTap)
for i in 1...120 {
    let u = Double(i) / 120
    let eased = u * u * (3 - 2 * u)
    let p = CGPoint(x: from.x + (to.x - from.x) * eased, y: from.y + (to.y - from.y) * eased)
    CGEvent(mouseEventSource: nil, mouseType: .leftMouseDragged, mouseCursorPosition: p, mouseButton: .left)?.post(tap: .cghidEventTap)
    usleep(23_333)
}
CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: to, mouseButton: .left)?.post(tap: .cghidEventTap)
