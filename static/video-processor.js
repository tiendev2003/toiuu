/**
 * Client-side video processing utilities
 * Giúp tối ưu hóa video trước khi gửi lên server
 */

class VideoProcessor {
    constructor() {
        this.supportedFormats = ['video/webm', 'video/mp4'];
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        this.maxDuration = 30; // 30 seconds
    }

    /**
     * Kiểm tra và tối ưu hóa video blob trước khi upload
     */
    async optimizeVideoBlob(blob, filename) {
        console.log(`[VideoProcessor] Processing ${filename}, size: ${(blob.size / 1024 / 1024).toFixed(2)}MB`);
        
        // Kiểm tra kích thước file
        if (blob.size > this.maxFileSize) {
            console.warn(`[VideoProcessor] File size too large: ${(blob.size / 1024 / 1024).toFixed(2)}MB`);
            throw new Error(`File size exceeds ${this.maxFileSize / 1024 / 1024}MB limit`);
        }

        // Kiểm tra format
        if (!this.supportedFormats.includes(blob.type)) {
            console.warn(`[VideoProcessor] Unsupported format: ${blob.type}`);
            throw new Error(`Unsupported video format: ${blob.type}`);
        }

        // Tạo video element để kiểm tra duration
        const videoElement = document.createElement('video');
        const videoUrl = URL.createObjectURL(blob);
        
        return new Promise((resolve, reject) => {
            videoElement.onloadedmetadata = () => {
                URL.revokeObjectURL(videoUrl);
                
                if (videoElement.duration > this.maxDuration) {
                    console.warn(`[VideoProcessor] Video too long: ${videoElement.duration}s`);
                    reject(new Error(`Video duration exceeds ${this.maxDuration}s limit`));
                    return;
                }

                console.log(`[VideoProcessor] Video validated: ${videoElement.duration.toFixed(2)}s, ${videoElement.videoWidth}x${videoElement.videoHeight}`);
                
                // Nếu là WebM và có vấn đề tương thích, thêm metadata
                if (blob.type === 'video/webm') {
                    resolve(this.enhanceWebMBlob(blob, filename, videoElement));
                } else {
                    resolve(blob);
                }
            };

            videoElement.onerror = () => {
                URL.revokeObjectURL(videoUrl);
                reject(new Error('Cannot load video for validation'));
            };

            videoElement.src = videoUrl;
        });
    }

    /**
     * Cải thiện WebM blob để tương thích tốt hơn với server
     */
    async enhanceWebMBlob(blob, filename, videoElement) {
        // Thêm thông tin metadata vào filename để server biết cách xử lý
        const enhancedFilename = filename.replace('.webm', `_${videoElement.videoWidth}x${videoElement.videoHeight}_${Math.round(videoElement.duration * 10) / 10}s.webm`);
        
        // Tạo File object mới với metadata
        const enhancedFile = new File([blob], enhancedFilename, {
            type: 'video/webm',
            lastModified: Date.now()
        });

        console.log(`[VideoProcessor] Enhanced WebM: ${enhancedFilename}`);
        return enhancedFile;
    }

    /**
     * Xử lý nhiều video blobs song song
     */
    async processVideoBlobs(videoBlobs) {
        console.log(`[VideoProcessor] Processing ${videoBlobs.length} video blobs`);
        
        const results = [];
        const errors = [];

        for (let i = 0; i < videoBlobs.length; i++) {
            try {
                const filename = `video_${i}.webm`;
                const response = await fetch(videoBlobs[i]);
                const blob = await response.blob();
                
                const optimizedBlob = await this.optimizeVideoBlob(blob, filename);
                results.push(optimizedBlob);
            } catch (error) {
                console.error(`[VideoProcessor] Error processing video ${i}:`, error);
                errors.push({ index: i, error: error.message });
            }
        }

        if (errors.length > 0) {
            console.warn(`[VideoProcessor] ${errors.length} videos failed processing:`, errors);
        }

        console.log(`[VideoProcessor] Successfully processed ${results.length}/${videoBlobs.length} videos`);
        return { results, errors };
    }

    /**
     * Tạo FormData với video files đã được tối ưu
     */
    async createOptimizedFormData(videoBlobs, additionalData = {}) {
        const { results: optimizedVideos, errors } = await this.processVideoBlobs(videoBlobs);
        
        if (optimizedVideos.length === 0) {
            throw new Error('No videos could be processed successfully');
        }

        const formData = new FormData();
        
        // Thêm videos
        optimizedVideos.forEach((video, index) => {
            formData.append('files', video);
        });

        // Thêm additional data
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        // Thêm metadata về processing
        formData.append('client_processing_info', JSON.stringify({
            original_count: videoBlobs.length,
            processed_count: optimizedVideos.length,
            errors: errors,
            processing_timestamp: Date.now()
        }));

        return formData;
    }
}

// Usage example:
/*
const videoProcessor = new VideoProcessor();

// Process videos before sending
const formData = await videoProcessor.createOptimizedFormData(videosToProcess, {
    frame_type: selectedFrameType,
    duration: videoDuration,
    mediaSessionCode: sessionCode
});

// Send to server
const response = await fetch('/api/process-video', {
    method: 'POST',
    body: formData
});
*/

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoProcessor;
}
