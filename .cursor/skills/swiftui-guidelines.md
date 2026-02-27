---
name: swiftui-guidelines
description: SwiftUI Technical Encyclopedia: Observation Framework, Structural Identity, Layout Processing, and Swift 6 Concurrency.
---

# Skill: SwiftUI Guidelines (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and construction of modern iOS and macOS user interfaces using the SwiftUI framework in the 2025 ecosystem. This document defines the standards for the Observation framework, structural identity math, and high-safety Swift 6 concurrency patterns.

---

## 1. State Management (Observation Framework)
Standardizing on the modern, high-performance `@Observable` macro (iOS 17+).

### 1.1 Observation Protocols
*   **Logic:** Replacing the legacy `ObservableObject` and `@Published` with the `@Observable` macro to ensure that only the views actually consuming a specific property are re-rendered.
*   **State Localization:** Utilizing `@State` for local, view-owned state and `@Environment` for shared, global dependency injection.

### 1.2 Implementation Protocol (Modern ViewModel)
```swift
@Observable
class UserProfileViewModel {
    var username: String = ""
    var isVerified: Bool = false
    
    # 1.2.1 Async Data Fetching (Swift 6)
    func fetchData() async {
        # Execution on @MainActor implicitly via @Observable in 2025
    }
}
```

---

## 2. Structural Identity & Layout Math
Understanding how SwiftUI determines what changed and how to render it.

### 2.1 Structural vs. Explicit Identity
*   **Logic:** SwiftUI identifies views by their position in the view hierarchy (Implicit) rather than a unique ID (Explicit).
*   **Constraint:** Avoiding `AnyView` and complex `if...else` statements that break structural identity and cause expensive "Identity Reset" redraws.

### 2.2 Layout Processing Standard (The 3-Step Dance)
1.  **Proposed Size:** The parent proposes a size to the child.
2.  **Chosen Size:** The child chooses its own size (e.g., `fixedSize()` or `aspectRatio()`).
3.  **Positioning:** The parent places the child in its coordinate space.
*   **Optimization:** Utilizing `Layout` protocol for complex, custom geometries that bypass the standard stack overhead.

---

## 3. Swift 6 Concurrency & UI Safety
Standardizing on "Zero-Race" multi-threaded GUI development.

### 3.1 `@MainActor` & `Sendable` Standards
*   **Logic:** Ensuring all UI-modifying code is strictly isolated to the Main Actor.
*   **Protocol:** Mandatory use of `Sendable` for data models passed between async contexts to prevent memory corruption.

---

## 4. Technical Appendix: SwiftUI Reference
| Component | Technical Implementation | Purpose |
| :--- | :--- | :--- |
| **@State** | View-local thread-safety | Mutability |
| **@Bindable** | Two-way @Observable link | Binding |
| **@AppStorage**| UserDefaults persistence | Config |
| **AnyView** | Type-erasure (Avoid) | Performance |

---

## 5. Industrial Case Study: High-Concurrency Trading App
**Objective:** Building a dashboard that updates 100+ stock prices per second.
1.  **State:** Using `@Observable` on a background-fetching service.
2.  **Throttling:** Utilizing `Task.sleep` and `TaskGroup` to batch UI updates every 16ms (60fps).
3.  **Visualization:** Using `Swift Charts` with direct `@Observable` bindings for hardware-accelerated rendering.
4.  **Verification:** Zero Main Thread hitches during extreme market volatility.

---

## 6. Glossary of SwiftUI Terms
*   **Declarative UI:** Describing WHAT the UI should look like, rather than HOW to build it.
*   **Reconciliation:** The process by which SwiftUI compares the old and new view trees.
*   **Modifier:** A function that wraps a view to change its appearance or behavior.
*   **Property Wrapper:** A custom type that adds behavior to a property (e.g., `@State`).

---

## 7. Mathematical Foundations: The View Value
*   **Logic:** SwiftUI views are structs, not objects. The "Computation" of a view is a simple $O(1)$ value-copy.
*   **Complexity:** The real cost is in the "Diff" algorithm. Targeting shallow view hierarchies to minimize diffing latency.

---

## 8. Troubleshooting & Performance Verification
*   **Stuttering Animations:** Occurs when the main thread is blocked by non-UI logic. *Fix: Move logic to a background `Task` and use `@MainActor` for results.*
*   **State Not Updating:** Accidental use of `@State` for an external object. *Fix: Use `@Observable` or `@Bindable`.*

---

## 9. Appendix: Future "Spatial" UI
*   **visionOS Standards:** Designing for depth, glassmorphism, and gaze-based interaction using `RealityKit` and `SwiftUI` in a unified 3D-aware coordinate system.

---

## 10. Benchmarks & Performance Standards (2025)
*   **UI Response Time:** Target < 10ms for interaction feedback.
*   **Build Time:** Target < 5s for incremental SwiftUI previews on modern MacBook Pro M3.

---

## 11. iOS 18 SwiftUI Enhancements
New features available in iOS 18 for enhanced UI development:

### 11.1 Floating Tab Bar
```swift
TabView {
    Tab("Home", systemImage: "house") {
        HomeView()
    }
    Tab("Settings", systemImage: "gear") {
        SettingsView()
    }
}
.tabViewStyle(.sidebarAdaptable) // Floats & transitions to sidebar
```

### 11.2 Mesh Gradients
```swift
MeshGradient(
    width: 3,
    height: 3,
    points: [
        [0, 0], [0.5, 0], [1, 0],
        [0, 0.5], [0.5, 0.5], [1, 0.5],
        [0, 1], [0.5, 1], [1, 1]
    ],
    colors: [
        .red, .orange, .yellow,
        .green, .blue, .purple,
        .pink, .mint, .cyan
    ]
)
```

### 11.3 Enhanced Scroll View Control
```swift
ScrollView {
    LazyVStack {
        ForEach(items) { item in
            ItemView(item: item)
        }
    }
}
.onScrollGeometryChange(for: CGFloat.self) { geo in
    geo.contentOffset.y
} action: { oldOffset, newOffset in
    // React to scroll position changes
}
```

---

## 12. Swift 6 Concurrency Best Practices
Strict concurrency checking for data race safety:

### 12.1 Incremental Adoption
```swift
// In Build Settings: Strict Concurrency Checking = Complete
// Migrate module by module, not entire project at once
```

### 12.2 Actor Design Guidelines
*   **Single Responsibility:** Keep actors focused on one concern.
*   **Minimize Cross-Actor Calls:** Reduce `await` points between actors.
*   **Use Value Types:** Pass value types between actors for safety.

### 12.3 @MainActor for UI
```swift
@MainActor
class ProfileViewModel: ObservableObject {
    @Published var name: String = ""
    
    func updateProfile() async {
        // Already on MainActor - safe to update @Published
        name = await fetchName()
    }
}
```

### 12.4 Sendable Conformance
```swift
// Value types are implicitly Sendable
struct UserData: Sendable {
    let id: UUID
    let name: String
}

// Reference types need explicit conformance
final class Cache: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: [String: Data] = [:]
}
```

---

## 13. Performance Optimization Protocols

### 13.1 Lazy Stacks for Large Datasets
```swift
ScrollView {
    LazyVStack(spacing: 8) {
        ForEach(items, id: \.id) { item in
            ItemRow(item: item)
        }
    }
}
```

### 13.2 Minimize View Recomputations
*   Keep `@State` variables small and focused.
*   Extract static subviews to prevent unnecessary redraws.
*   Use `equatable()` modifier for complex views.

### 13.3 Profile with Instruments
*   Use Time Profiler for CPU bottlenecks.
*   Use SwiftUI Hangs instrument for UI freezes.
*   Target < 8ms per frame (120fps on ProMotion).

---

## 14. Preview-Driven Development
Integrate SwiftUI Previews into core workflow:

```swift
#Preview("Light Mode") {
    ProfileView(viewModel: .preview)
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    ProfileView(viewModel: .preview)
        .preferredColorScheme(.dark)
}

#Preview("Landscape") {
    ProfileView(viewModel: .preview)
        .previewInterfaceOrientation(.landscapeLeft)
}
```

---

## 15. Dynamic Island & Live Activities
```swift
struct DeliveryLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: DeliveryAttributes.self) { context in
            // Lock Screen view
            DeliveryLockScreenView(context: context)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Image(systemName: "truck")
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text(context.state.eta)
                }
            } compactLeading: {
                Image(systemName: "truck")
            } compactTrailing: {
                Text(context.state.eta)
            } minimal: {
                Image(systemName: "truck")
            }
        }
    }
}
```

---

## 16. Human Interface Guidelines Compliance
*   Follow Apple HIG for native feel.
*   Use SF Symbols for consistent iconography.
*   Support Dynamic Type for accessibility.
*   Implement dark mode properly.

---

[Back to README](../../README.md)
