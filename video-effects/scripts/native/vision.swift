import Foundation
import Vision
import CoreImage
import AppKit
let args=CommandLine.arguments
if args.count != 4 { fatalError("Usage: vision segment|track INPUT_FRAMES OUTPUT_FOLDER") }
let mode=args[1], input=URL(fileURLWithPath:args[2]), output=URL(fileURLWithPath:args[3])
let files=try FileManager.default.contentsOfDirectory(at:input,includingPropertiesForKeys:nil).filter{$0.pathExtension=="png"}.sorted{$0.lastPathComponent<$1.lastPathComponent}
try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
let ci=CIContext(options:[.useSoftwareRenderer:false])
let segment=VNGeneratePersonSegmentationRequest();segment.qualityLevel = .accurate;segment.outputPixelFormat=kCVPixelFormatType_OneComponent8
let hand=VNDetectHumanHandPoseRequest();hand.maximumHandCount=2
var observations:[[String:Any]]=[]
for (index,file) in files.enumerated(){try autoreleasepool{
 guard let image=CIImage(contentsOf:file),let cg=ci.createCGImage(image,from:image.extent) else{throw NSError(domain:"Image",code:1)}
 let request=VNImageRequestHandler(cgImage:cg,options:[:])
 if mode=="segment" {
  try request.perform([segment]);guard let buffer=segment.results?.first?.pixelBuffer else{throw NSError(domain:"Segmentation",code:2)}
  var mask=CIImage(cvPixelBuffer:buffer);mask=mask.transformed(by:CGAffineTransform(scaleX:image.extent.width/mask.extent.width,y:image.extent.height/mask.extent.height))
  let clear=CIImage(color:.clear).cropped(to:image.extent)
  let merged=image.applyingFilter("CIBlendWithMask",parameters:[kCIInputBackgroundImageKey:clear,kCIInputMaskImageKey:mask])
  try ci.writePNGRepresentation(of:merged,to:output.appendingPathComponent(file.lastPathComponent),format:.RGBA8,colorSpace:CGColorSpaceCreateDeviceRGB(),options:[:])
 }else if mode=="track"{
  try request.perform([hand]);var hands:[[String:Any]]=[]
  for observation in hand.results ?? []{
   let points=try observation.recognizedPoints(.all)
   var values:[String:[String:Double]]=[:]
   for (joint,point) in points {values[joint == .wrist ? "wrist" : (joint == .indexTip ? "indexTip" : joint.rawValue.rawValue)]=["x":Double(point.location.x),"y":1-Double(point.location.y),"confidence":Double(point.confidence)]}
   hands.append(["points":values,"confidence":Double(observation.confidence)])
  }
  observations.append(["frame":index,"hands":hands])
 }else {throw NSError(domain:"UnknownMode",code:3)}
}}
if mode=="track"{let data=try JSONSerialization.data(withJSONObject:observations,options:[.sortedKeys]);try data.write(to:output.appendingPathComponent("landmarks.json"))}
print("Processed \(files.count) frames")
